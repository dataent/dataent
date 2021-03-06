# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# Database Module
# --------------------

from __future__ import unicode_literals
import warnings
import datetime
import dataent
import dataent.defaults
from time import time
import re
import dataent.model.meta
from dataent.utils import now, get_datetime, cstr, cast_fieldtype
from dataent import _
from dataent.model.utils.link_count import flush_local_link_count
from dataent.model.utils import STANDARD_FIELD_CONVERSION_MAP
from dataent.utils.background_jobs import execute_job, get_queue
from dataent import as_unicode
import six

# imports - compatibility imports
from six import (
	integer_types,
	string_types,
	binary_type,
	text_type,
	iteritems
)

# imports - third-party imports
from markdown2 import UnicodeWithAttrs
from pymysql.times import TimeDelta
from pymysql.constants 	import ER, FIELD_TYPE
from pymysql.converters import conversions
import pymysql

# Helpers
def _cast_result(doctype, result):
	batch = [ ]

	try:
		for field, value in result:
			df = dataent.get_meta(doctype).get_field(field)
			if df:
				value = cast_fieldtype(df.fieldtype, value)

			batch.append(tuple([field, value]))
	except dataent.exceptions.DoesNotExistError:
		return result

	return tuple(batch)

class Database:
	"""
	   Open a database connection with the given parmeters, if use_default is True, use the
	   login details from `conf.py`. This is called by the request handler and is accessible using
	   the `db` global variable. the `sql` method is also global to run queries
	"""
	def __init__(self, host=None, user=None, password=None, ac_name=None, use_default = 0, local_infile = 0):
		self.host = host or dataent.conf.db_host or 'localhost'
		self.user = user or dataent.conf.db_name
		self._conn = None

		if ac_name:
			self.user = self.get_db_login(ac_name) or dataent.conf.db_name

		if use_default:
			self.user = dataent.conf.db_name

		self.transaction_writes = 0
		self.auto_commit_on_many_writes = 0

		self.password = password or dataent.conf.db_password
		self.value_cache = {}

		# this param is to load CSV's with LOCAL keyword.
		# it can be set in site_config as > bench set-config local_infile 1
		# once the local-infile is set on MySql Server, the client needs to connect with this option
		# Connections without this option leads to: 'The used command is not allowed with this MariaDB version' error
		self.local_infile = local_infile or dataent.conf.local_infile

	def get_db_login(self, ac_name):
		return ac_name

	def connect(self):
		"""Connects to a database as set in `site_config.json`."""
		warnings.filterwarnings('ignore', category=pymysql.Warning)
		usessl = 0
		if dataent.conf.db_ssl_ca and dataent.conf.db_ssl_cert and dataent.conf.db_ssl_key:
			usessl = 1
			self.ssl = {
				'ca':dataent.conf.db_ssl_ca,
				'cert':dataent.conf.db_ssl_cert,
				'key':dataent.conf.db_ssl_key
			}

		conversions.update({
			FIELD_TYPE.NEWDECIMAL: float,
			FIELD_TYPE.DATETIME: get_datetime,
			UnicodeWithAttrs: conversions[text_type]
		})

		if six.PY2:
			conversions.update({
				TimeDelta: conversions[binary_type]
			})

		if usessl:
			self._conn = pymysql.connect(self.host, self.user or '', self.password or '',
				charset='utf8mb4', use_unicode = True, ssl=self.ssl, conv = conversions, local_infile = self.local_infile)
		else:
			self._conn = pymysql.connect(self.host, self.user or '', self.password or '',
				charset='utf8mb4', use_unicode = True, conv = conversions, local_infile = self.local_infile)

		# MYSQL_OPTION_MULTI_STATEMENTS_OFF = 1
		# # self._conn.set_server_option(MYSQL_OPTION_MULTI_STATEMENTS_OFF)

		self._cursor = self._conn.cursor()
		if self.user != 'root':
			self.use(self.user)
		dataent.local.rollback_observers = []

	def use(self, db_name):
		"""`USE` db_name."""
		self._conn.select_db(db_name)
		self.cur_db_name = db_name

	def validate_query(self, q):
		"""Throw exception for dangerous queries: `ALTER`, `DROP`, `TRUNCATE` if not `Administrator`."""
		cmd = q.strip().lower().split()[0]
		if cmd in ['alter', 'drop', 'truncate'] and dataent.session.user != 'Administrator':
			dataent.throw(_("Not permitted"), dataent.PermissionError)

	def sql(self, query, values=(), as_dict = 0, as_list = 0, formatted = 0,
		debug=0, ignore_ddl=0, as_utf8=0, auto_commit=0, update=None, explain=False):
		"""Execute a SQL query and fetch all rows.

		:param query: SQL query.
		:param values: List / dict of values to be escaped and substituted in the query.
		:param as_dict: Return as a dictionary.
		:param as_list: Always return as a list.
		:param formatted: Format values like date etc.
		:param debug: Print query and `EXPLAIN` in debug log.
		:param ignore_ddl: Catch exception if table, column missing.
		:param as_utf8: Encode values as UTF 8.
		:param auto_commit: Commit after executing the query.
		:param update: Update this dict to all rows (if returned `as_dict`).

		Examples:

			# return customer names as dicts
			dataent.db.sql("select name from tabCustomer", as_dict=True)

			# return names beginning with a
			dataent.db.sql("select name from tabCustomer where name like %s", "a%")

			# values as dict
			dataent.db.sql("select name from tabCustomer where name like %(name)s and owner=%(owner)s",
				{"name": "a%", "owner":"test@example.com"})

		"""
		if not self._conn:
			self.connect()

		# in transaction validations
		self.check_transaction_status(query)

		# autocommit
		if auto_commit: self.commit()

		# execute
		try:
			if debug:
				time_start = time()

			if values!=():
				if isinstance(values, dict):
					values = dict(values)

				# MySQL-python==1.2.5 hack!
				if not isinstance(values, (dict, tuple, list)):
					values = (values,)

				if debug and query.strip().lower().startswith('select'):
					try:
						if explain:
							self.explain_query(query, values)
						dataent.errprint(query % values)
					except TypeError:
						dataent.errprint([query, values])
				if (dataent.conf.get("logging") or False)==2:
					dataent.log("<<<< query")
					dataent.log(query)
					dataent.log("with values:")
					dataent.log(values)
					dataent.log(">>>>")
				self._cursor.execute(query, values)

				if dataent.flags.in_migrate:
					self.log_touched_tables(query, values)

			else:
				if debug:
					if explain:
						self.explain_query(query)
					dataent.errprint(query)
				if (dataent.conf.get("logging") or False)==2:
					dataent.log("<<<< query")
					dataent.log(query)
					dataent.log(">>>>")

				self._cursor.execute(query)

				if dataent.flags.in_migrate:
					self.log_touched_tables(query)

			if debug:
				time_end = time()
				dataent.errprint(("Execution time: {0} sec").format(round(time_end - time_start, 2)))

		except Exception as e:
			if ignore_ddl and e.args[0] in (ER.BAD_FIELD_ERROR, ER.NO_SUCH_TABLE,
				ER.CANT_DROP_FIELD_OR_KEY):
				pass

			# NOTE: causes deadlock
			# elif e.args[0]==2006:
			# 	# mysql has gone away
			# 	self.connect()
			# 	return self.sql(query=query, values=values,
			# 		as_dict=as_dict, as_list=as_list, formatted=formatted,
			# 		debug=debug, ignore_ddl=ignore_ddl, as_utf8=as_utf8,
			# 		auto_commit=auto_commit, update=update)
			else:
				raise

		if auto_commit: self.commit()

		# scrub output if required
		if as_dict:
			ret = self.fetch_as_dict(formatted, as_utf8)
			if update:
				for r in ret:
					r.update(update)
			return ret
		elif as_list:
			return self.convert_to_lists(self._cursor.fetchall(), formatted, as_utf8)
		elif as_utf8:
			return self.convert_to_lists(self._cursor.fetchall(), formatted, as_utf8)
		else:
			return self._cursor.fetchall()

	def explain_query(self, query, values=None):
		"""Print `EXPLAIN` in error log."""
		try:
			dataent.errprint("--- query explain ---")
			if values is None:
				self._cursor.execute("explain " + query)
			else:
				self._cursor.execute("explain " + query, values)
			import json
			dataent.errprint(json.dumps(self.fetch_as_dict(), indent=1))
			dataent.errprint("--- query explain end ---")
		except:
			dataent.errprint("error in query explain")

	def sql_list(self, query, values=(), debug=False):
		"""Return data as list of single elements (first column).

		Example:

			# doctypes = ["DocType", "DocField", "User", ...]
			doctypes = dataent.db.sql_list("select name from DocType")
		"""
		return [r[0] for r in self.sql(query, values, debug=debug)]

	def sql_ddl(self, query, values=(), debug=False):
		"""Commit and execute a query. DDL (Data Definition Language) queries that alter schema
		autocommit in MariaDB."""
		self.commit()
		self.sql(query, debug=debug)

	def check_transaction_status(self, query):
		"""Raises exception if more than 20,000 `INSERT`, `UPDATE` queries are
		executed in one transaction. This is to ensure that writes are always flushed otherwise this
		could cause the system to hang."""
		if self.transaction_writes and \
			query and query.strip().split()[0].lower() in ['start', 'alter', 'drop', 'create', "begin", "truncate"]:
			raise Exception('This statement can cause implicit commit')

		if query and query.strip().lower() in ('commit', 'rollback'):
			self.transaction_writes = 0

		if query[:6].lower() in ('update', 'insert', 'delete'):
			self.transaction_writes += 1
			if self.transaction_writes > 200000:
				if self.auto_commit_on_many_writes:
					dataent.db.commit()
				else:
					dataent.throw(_("Too many writes in one request. Please send smaller requests"), dataent.ValidationError)

	def fetch_as_dict(self, formatted=0, as_utf8=0):
		"""Internal. Converts results to dict."""
		result = self._cursor.fetchall()
		ret = []
		needs_formatting = self.needs_formatting(result, formatted)
		if result:
			keys = [column[0] for column in self._cursor.description]

		for r in result:
			values = []
			for i in range(len(r)):
				if needs_formatting:
					val = self.convert_to_simple_type(r[i], formatted)
				else:
					val = r[i]

				if as_utf8 and type(val) is text_type:
					val = val.encode('utf-8')
				values.append(val)

			ret.append(dataent._dict(zip(keys, values)))
		return ret

	def needs_formatting(self, result, formatted):
		"""Returns true if the first row in the result has a Date, Datetime, Long Int."""
		if result and result[0]:
			for v in result[0]:
				if isinstance(v, (datetime.date, datetime.timedelta, datetime.datetime, integer_types)):
					return True
				if formatted and isinstance(v, (int, float)):
					return True

		return False

	def get_description(self):
		"""Returns result metadata."""
		return self._cursor.description

	def convert_to_simple_type(self, v, formatted=0):
		"""Format date, time, longint values."""
		return v

		from dataent.utils import formatdate, fmt_money

		if isinstance(v, (datetime.date, datetime.timedelta, datetime.datetime, integer_types)):
			if isinstance(v, datetime.date):
				v = text_type(v)
				if formatted:
					v = formatdate(v)

			# time
			elif isinstance(v, (datetime.timedelta, datetime.datetime)):
				v = text_type(v)

			# long
			elif isinstance(v, integer_types):
				v=int(v)

		# convert to strings... (if formatted)
		if formatted:
			if isinstance(v, float):
				v=fmt_money(v)
			elif isinstance(v, int):
				v = text_type(v)

		return v

	def convert_to_lists(self, res, formatted=0, as_utf8=0):
		"""Convert tuple output to lists (internal)."""
		nres = []
		needs_formatting = self.needs_formatting(res, formatted)
		for r in res:
			nr = []
			for c in r:
				if needs_formatting:
					val = self.convert_to_simple_type(c, formatted)
				else:
					val = c
				if as_utf8 and type(val) is text_type:
					val = val.encode('utf-8')
				nr.append(val)
			nres.append(nr)
		return nres

	def convert_to_utf8(self, res, formatted=0):
		"""Encode result as UTF-8."""
		nres = []
		for r in res:
			nr = []
			for c in r:
				if type(c) is text_type:
					c = c.encode('utf-8')
					nr.append(self.convert_to_simple_type(c, formatted))
			nres.append(nr)
		return nres

	def build_conditions(self, filters):
		"""Convert filters sent as dict, lists to SQL conditions. filter's key
		is passed by map function, build conditions like:

		* ifnull(`fieldname`, default_value) = %(fieldname)s
		* `fieldname` [=, !=, >, >=, <, <=] %(fieldname)s
		"""
		conditions = []
		values = {}
		def _build_condition(key):
			"""
				filter's key is passed by map function
				build conditions like:
					* ifnull(`fieldname`, default_value) = %(fieldname)s
					* `fieldname` [=, !=, >, >=, <, <=] %(fieldname)s
			"""
			_operator = "="
			_rhs = " %(" + key + ")s"
			value = filters.get(key)
			values[key] = value
			if isinstance(value, (list, tuple)):
				# value is a tuble like ("!=", 0)
				_operator = value[0]
				values[key] = value[1]
				if isinstance(value[1], (tuple, list)):
					# value is a list in tuple ("in", ("A", "B"))
					inner_list = []
					for i, v in enumerate(value[1]):
						inner_key = "{0}_{1}".format(key, i)
						values[inner_key] = v
						inner_list.append("%({0})s".format(inner_key))

					_rhs = " ({0})".format(", ".join(inner_list))
					del values[key]

			if _operator not in ["=", "!=", ">", ">=", "<", "<=", "like", "in", "not in", "not like"]:
				_operator = "="

			if "[" in key:
				split_key = key.split("[")
				condition = "ifnull(`" + split_key[0] + "`, " + split_key[1][:-1] + ") " \
					+ _operator + _rhs
			else:
				condition = "`" + key + "` " + _operator + _rhs

			conditions.append(condition)

		if isinstance(filters, int):
			# docname is a number, convert to string
			filters = str(filters)

		if isinstance(filters, string_types):
			filters = { "name": filters }

		for f in filters:
			_build_condition(f)

		return " and ".join(conditions), values

	def get(self, doctype, filters=None, as_dict=True, cache=False):
		"""Returns `get_value` with fieldname='*'"""
		return self.get_value(doctype, filters, "*", as_dict=as_dict, cache=cache)

	def get_value(self, doctype, filters=None, fieldname="name", ignore=None, as_dict=False,
		debug=False, order_by=None, cache=False):
		"""Returns a document property or list of properties.

		:param doctype: DocType name.
		:param filters: Filters like `{"x":"y"}` or name of the document. `None` if Single DocType.
		:param fieldname: Column name.
		:param ignore: Don't raise exception if table, column is missing.
		:param as_dict: Return values as dict.
		:param debug: Print query in error log.
		:param order_by: Column to order by

		Example:

			# return first customer starting with a
			dataent.db.get_value("Customer", {"name": ("like a%")})

			# return last login of **User** `test@example.com`
			dataent.db.get_value("User", "test@example.com", "last_login")

			last_login, last_ip = dataent.db.get_value("User", "test@example.com",
				["last_login", "last_ip"])

			# returns default date_format
			dataent.db.get_value("System Settings", None, "date_format")
		"""

		ret = self.get_values(doctype, filters, fieldname, ignore, as_dict, debug,
			order_by, cache=cache)

		return ((len(ret[0]) > 1 or as_dict) and ret[0] or ret[0][0]) if ret else None

	def get_values(self, doctype, filters=None, fieldname="name", ignore=None, as_dict=False,
		debug=False, order_by=None, update=None, cache=False):
		"""Returns multiple document properties.

		:param doctype: DocType name.
		:param filters: Filters like `{"x":"y"}` or name of the document.
		:param fieldname: Column name.
		:param ignore: Don't raise exception if table, column is missing.
		:param as_dict: Return values as dict.
		:param debug: Print query in error log.
		:param order_by: Column to order by

		Example:

			# return first customer starting with a
			customers = dataent.db.get_values("Customer", {"name": ("like a%")})

			# return last login of **User** `test@example.com`
			user = dataent.db.get_values("User", "test@example.com", "*")[0]
		"""
		out = None
		if cache and isinstance(filters, string_types) and \
			(doctype, filters, fieldname) in self.value_cache:
			return self.value_cache[(doctype, filters, fieldname)]

		if not order_by: order_by = 'modified desc'

		if isinstance(filters, list):
			out = self._get_value_for_many_names(doctype, filters, fieldname, debug=debug)

		else:
			fields = fieldname
			if fieldname!="*":
				if isinstance(fieldname, string_types):
					fields = [fieldname]
				else:
					fields = fieldname

			if (filters is not None) and (filters!=doctype or doctype=="DocType"):
				try:
					out = self._get_values_from_table(fields, filters, doctype, as_dict, debug, order_by, update)
				except Exception as e:
					if ignore and e.args[0] in (1146, 1054):
						# table or column not found, return None
						out = None
					elif (not ignore) and e.args[0]==1146:
						# table not found, look in singles
						out = self.get_values_from_single(fields, filters, doctype, as_dict, debug, update)
					else:
						raise
			else:
				out = self.get_values_from_single(fields, filters, doctype, as_dict, debug, update)

		if cache and isinstance(filters, string_types):
			self.value_cache[(doctype, filters, fieldname)] = out

		return out

	def get_values_from_single(self, fields, filters, doctype, as_dict=False, debug=False, update=None):
		"""Get values from `tabSingles` (Single DocTypes) (internal).

		:param fields: List of fields,
		:param filters: Filters (dict).
		:param doctype: DocType name.
		"""
		# TODO
		# if not dataent.model.meta.is_single(doctype):
		# 	raise dataent.DoesNotExistError("DocType", doctype)

		if fields=="*" or isinstance(filters, dict):
			# check if single doc matches with filters
			values = self.get_singles_dict(doctype)
			if isinstance(filters, dict):
				for key, value in filters.items():
					if values.get(key) != value:
						return []

			if as_dict:
				return values and [values] or []

			if isinstance(fields, list):
				return [map(lambda d: values.get(d), fields)]

		else:
			r = self.sql("""select field, value
				from tabSingles where field in (%s) and doctype=%s""" \
					% (', '.join(['%s'] * len(fields)), '%s'),
					tuple(fields) + (doctype,), as_dict=False, debug=debug)
			# r = _cast_result(doctype, r)

			if as_dict:
				if r:
					r = dataent._dict(r)
					if update:
						r.update(update)
					return [r]
				else:
					return []
			else:
				return r and [[i[1] for i in r]] or []

	def get_singles_dict(self, doctype, debug = False):
		"""Get Single DocType as dict.

		:param doctype: DocType of the single object whose value is requested

		Example:

			# Get coulmn and value of the single doctype Accounts Settings
			account_settings = dataent.db.get_singles_dict("Accounts Settings")
		"""
		result = self.sql("""
			SELECT field, value
			FROM   `tabSingles`
			WHERE  doctype = %s
		""", doctype)
		# result = _cast_result(doctype, result)

		dict_  = dataent._dict(result)

		return dict_

	def get_all(self, *args, **kwargs):
		return dataent.get_all(*args, **kwargs)

	def get_list(self, *args, **kwargs):
		return dataent.get_list(*args, **kwargs)

	def get_single_value(self, doctype, fieldname, cache=False):
		"""Get property of Single DocType. Cache locally by default

		:param doctype: DocType of the single object whose value is requested
		:param fieldname: `fieldname` of the property whose value is requested

		Example:

			# Get the default value of the company from the Global Defaults doctype.
			company = dataent.db.get_single_value('Global Defaults', 'default_company')
		"""

		if not doctype in self.value_cache:
			self.value_cache = self.value_cache[doctype] = {}

		if fieldname in self.value_cache[doctype]:
			return self.value_cache[doctype][fieldname]

		val = self.sql("""select value from
			tabSingles where doctype=%s and field=%s""", (doctype, fieldname))
		val = val[0][0] if val else None

		if val=="0" or val=="1":
			# check type
			val = int(val)

		self.value_cache[doctype][fieldname] = val

		return val

	def get_singles_value(self, *args, **kwargs):
		"""Alias for get_single_value"""
		return self.get_single_value(*args, **kwargs)

	def _get_values_from_table(self, fields, filters, doctype, as_dict, debug, order_by=None, update=None):
		fl = []
		if isinstance(fields, (list, tuple)):
			for f in fields:
				if "(" in f or " as " in f: # function
					fl.append(f)
				else:
					fl.append("`" + f + "`")
			fl = ", ".join(fl)
		else:
			fl = fields
			if fields=="*":
				as_dict = True

		conditions, values = self.build_conditions(filters)

		order_by = ("order by " + order_by) if order_by else ""

		r = self.sql("select {0} from `tab{1}` {2} {3} {4}"
			.format(fl, doctype, "where" if conditions else "", conditions, order_by), values,
			as_dict=as_dict, debug=debug, update=update)

		return r

	def _get_value_for_many_names(self, doctype, names, field, debug=False):
		names = list(filter(None, names))

		if names:
			return dict(self.sql("select name, `%s` from `tab%s` where name in (%s)" \
				% (field, doctype, ", ".join(["%s"]*len(names))), names, debug=debug))
		else:
			return {}

	def update(self, *args, **kwargs):
		"""Update multiple values. Alias for `set_value`."""
		return self.set_value(*args, **kwargs)

	def set_value(self, dt, dn, field, val, modified=None, modified_by=None,
		update_modified=True, debug=False):
		"""Set a single value in the database, do not call the ORM triggers
		but update the modified timestamp (unless specified not to).

		**Warning:** this function will not call Document events and should be avoided in normal cases.

		:param dt: DocType name.
		:param dn: Document name.
		:param field: Property / field name or dictionary of values to be updated
		:param value: Value to be updated.
		:param modified: Use this as the `modified` timestamp.
		:param modified_by: Set this user as `modified_by`.
		:param update_modified: default True. Set as false, if you don't want to update the timestamp.
		:param debug: Print the query in the developer / js console.
		"""
		if not modified:
			modified = now()
		if not modified_by:
			modified_by = dataent.session.user

		to_update = {}
		if update_modified:
			to_update = {"modified": modified, "modified_by": modified_by}

		if isinstance(field, dict):
			to_update.update(field)
		else:
			to_update.update({field: val})

		if dn and dt!=dn:
			# with table
			conditions, values = self.build_conditions(dn)

			values.update(to_update)

			set_values = []
			for key in to_update:
				set_values.append('`{0}`=%({0})s'.format(key))

			self.sql("""update `tab{0}`
				set {1} where {2}""".format(dt, ', '.join(set_values), conditions),
				values, debug=debug)

		else:
			# for singles
			keys = list(to_update)
			self.sql('''
				delete from tabSingles
				where field in ({0}) and
					doctype=%s'''.format(', '.join(['%s']*len(keys))),
					list(keys) + [dt], debug=debug)
			for key, value in iteritems(to_update):
				self.sql('''insert into tabSingles(doctype, field, value) values (%s, %s, %s)''',
					(dt, key, value), debug=debug)

		if dt in self.value_cache:
			del self.value_cache[dt]

		dataent.clear_document_cache(dt, dn)

	def set(self, doc, field, val):
		"""Set value in document. **Avoid**"""
		doc.db_set(field, val)

	def touch(self, doctype, docname):
		"""Update the modified timestamp of this document."""
		from dataent.utils import now
		modified = now()
		dataent.db.sql("""update `tab{doctype}` set `modified`=%s
			where name=%s""".format(doctype=doctype), (modified, docname))
		return modified

	def set_temp(self, value):
		"""Set a temperory value and return a key."""
		key = dataent.generate_hash()
		dataent.cache().hset("temp", key, value)
		return key

	def get_temp(self, key):
		"""Return the temperory value and delete it."""
		return dataent.cache().hget("temp", key)

	def set_global(self, key, val, user='__global'):
		"""Save a global key value. Global values will be automatically set if they match fieldname."""
		self.set_default(key, val, user)

	def get_global(self, key, user='__global'):
		"""Returns a global key value."""
		return self.get_default(key, user)

	def set_default(self, key, val, parent="__default", parenttype=None):
		"""Sets a global / user default value."""
		dataent.defaults.set_default(key, val, parent, parenttype)

	def add_default(self, key, val, parent="__default", parenttype=None):
		"""Append a default value for a key, there can be multiple default values for a particular key."""
		dataent.defaults.add_default(key, val, parent, parenttype)

	def get_default(self, key, parent="__default"):
		"""Returns default value as a list if multiple or single"""
		d = self.get_defaults(key, parent)
		return isinstance(d, list) and d[0] or d

	def get_defaults(self, key=None, parent="__default"):
		"""Get all defaults"""
		if key:
			defaults = dataent.defaults.get_defaults(parent)
			d = defaults.get(key, None)
			if(not d and key != dataent.scrub(key)):
				d = defaults.get(dataent.scrub(key), None)
			return d
		else:
			return dataent.defaults.get_defaults(parent)

	def begin(self):
		self.sql("start transaction")

	def commit(self):
		"""Commit current transaction. Calls SQL `COMMIT`."""
		self.sql("commit")
		dataent.local.rollback_observers = []
		self.flush_realtime_log()
		enqueue_jobs_after_commit()
		flush_local_link_count()

	def flush_realtime_log(self):
		for args in dataent.local.realtime_log:
			dataent.realtime.emit_via_redis(*args)

		dataent.local.realtime_log = []

	def rollback(self):
		"""`ROLLBACK` current transaction."""
		self.sql("rollback")
		self.begin()
		for obj in dataent.local.rollback_observers:
			if hasattr(obj, "on_rollback"):
				obj.on_rollback()
		dataent.local.rollback_observers = []

	def field_exists(self, dt, fn):
		"""Return true of field exists."""
		return self.sql("select name from tabDocField where fieldname=%s and parent=%s", (dt, fn))

	def table_exists(self, doctype):
		"""Returns True if table for given doctype exists."""
		return ("tab" + doctype) in self.get_tables()

	def get_tables(self):
		return [d[0] for d in self.sql("show tables")]

	def a_row_exists(self, doctype):
		"""Returns True if atleast one row exists."""
		return self.sql("select name from `tab{doctype}` limit 1".format(doctype=doctype))

	def exists(self, dt, dn=None, cache=False):
		"""Returns true if document exists.

		:param dt: DocType name.
		:param dn: Document name or filter dict."""
		if isinstance(dt, string_types):
			if dt!="DocType" and dt==dn:
				return True # single always exists (!)
			try:
				return self.get_value(dt, dn, "name", cache=cache)
			except:
				return None

		elif isinstance(dt, dict) and dt.get('doctype'):
			try:
				conditions = []
				for d in dt:
					if d == 'doctype': continue
					conditions.append('`%s` = "%s"' % (d, cstr(dt[d]).replace('"', '\"')))
				return self.sql('select name from `tab%s` where %s' % \
						(dt['doctype'], " and ".join(conditions)))
			except:
				return None

	def count(self, dt, filters=None, debug=False, cache=False):
		"""Returns `COUNT(*)` for given DocType and filters."""
		if cache and not filters:
			cache_count = dataent.cache().get_value('doctype:count:{}'.format(dt))
			if cache_count is not None:
				return cache_count
		if filters:
			conditions, filters = self.build_conditions(filters)
			count = dataent.db.sql("""select count(*)
				from `tab%s` where %s""" % (dt, conditions), filters, debug=debug)[0][0]
			return count
		else:
			count = dataent.db.sql("""select count(*)
				from `tab%s`""" % (dt,))[0][0]

			if cache:
				dataent.cache().set_value('doctype:count:{}'.format(dt), count, expires_in_sec = 86400)

			return count


	def get_creation_count(self, doctype, minutes):
		"""Get count of records created in the last x minutes"""
		from dataent.utils import now_datetime
		from dateutil.relativedelta import relativedelta

		return dataent.db.sql("""select count(name) from `tab{doctype}`
			where creation >= %s""".format(doctype=doctype),
			now_datetime() - relativedelta(minutes=minutes))[0][0]

	def get_db_table_columns(self, table):
		"""Returns list of column names from given table."""
		return [r[0] for r in self.sql("DESC `%s`" % table)]

	def get_table_columns(self, doctype):
		"""Returns list of column names from given doctype."""
		return self.get_db_table_columns('tab' + doctype)

	def has_column(self, doctype, column):
		"""Returns True if column exists in database."""
		return column in self.get_table_columns(doctype)

	def get_column_type(self, doctype, column):
		return dataent.db.sql('''SELECT column_type FROM INFORMATION_SCHEMA.COLUMNS
			WHERE table_name = 'tab{0}' AND COLUMN_NAME = "{1}"'''.format(doctype, column))[0][0]

	def add_index(self, doctype, fields, index_name=None):
		"""Creates an index with given fields if not already created.
		Index name will be `fieldname1_fieldname2_index`"""
		if not index_name:
			index_name = "_".join(fields) + "_index"

			# remove index length if present e.g. (10) from index name
			index_name = re.sub(r"\s*\([^)]+\)\s*", r"", index_name)

		if not dataent.db.sql("""show index from `tab%s` where Key_name="%s" """ % (doctype, index_name)):
			dataent.db.commit()
			dataent.db.sql("""alter table `tab%s`
				add index `%s`(%s)""" % (doctype, index_name, ", ".join(fields)))

	def add_unique(self, doctype, fields, constraint_name=None):
		if isinstance(fields, string_types):
			fields = [fields]
		if not constraint_name:
			constraint_name = "unique_" + "_".join(fields)

		if not dataent.db.sql("""select CONSTRAINT_NAME from information_schema.TABLE_CONSTRAINTS
			where table_name=%s and constraint_type='UNIQUE' and CONSTRAINT_NAME=%s""",
			('tab' + doctype, constraint_name)):
				dataent.db.commit()
				dataent.db.sql("""alter table `tab%s`
					add unique `%s`(%s)""" % (doctype, constraint_name, ", ".join(fields)))

	def get_system_setting(self, key):
		def _load_system_settings():
			return self.get_singles_dict("System Settings")
		return dataent.cache().get_value("system_settings", _load_system_settings).get(key)

	def close(self):
		"""Close database connection."""
		if self._conn:
			# self._cursor.close()
			self._conn.close()
			self._cursor = None
			self._conn = None

	def escape(self, s, percent=True):
		"""Excape quotes and percent in given string."""
		# pymysql expects unicode argument to escape_string with Python 3
		s = as_unicode(pymysql.escape_string(as_unicode(s)), "utf-8").replace("`", "\\`")

		# NOTE separating % escape, because % escape should only be done when using LIKE operator
		# or when you use python format string to generate query that already has a %s
		# for example: sql("select name from `tabUser` where name=%s and {0}".format(conditions), something)
		# defaulting it to True, as this is the most frequent use case
		# ideally we shouldn't have to use ESCAPE and strive to pass values via the values argument of sql
		if percent:
			s = s.replace("%", "%%")

		return s

	def get_descendants(self, doctype, name):
		'''Return descendants of the current record'''
		node_location_indexes = self.get_value(doctype, name, ('lft', 'rgt'))
		if node_location_indexes:
			lft, rgt = node_location_indexes
			return self.sql_list('''select name from `tab{doctype}`
				where lft > {lft} and rgt < {rgt}'''.format(doctype=doctype, lft=lft, rgt=rgt))
		else:
			# when document does not exist
			return []

	def log_touched_tables(self, query, values=None):
		if values:
			query = self._cursor.mogrify(query, values)
		if query.strip().lower().split()[0] in ('insert', 'delete', 'update', 'alter'):
			# single_word_regex is designed to match following patterns
			# `tabXxx`, tabXxx and "tabXxx"

			# multi_word_regex is designed to match following patterns
			# `tabXxx Xxx` and "tabXxx Xxx"

			# ([`"]?) Captures " or ` at the begining of the table name (if provided)
			# \1 matches the first captured group (quote character) at the end of the table name
			# multi word table name must have surrounding quotes.

			# (tab([A-Z]\w+)( [A-Z]\w+)*) Captures table names that start with "tab"
			# and are continued with multiple words that start with a captital letter
			# e.g. 'tabXxx' or 'tabXxx Xxx' or 'tabXxx Xxx Xxx' and so on

			single_word_regex = r'([`"]?)(tab([A-Z]\w+))\1'
			multi_word_regex = r'([`"])(tab([A-Z]\w+)( [A-Z]\w+)+)\1'
			tables = []
			for regex in (single_word_regex, multi_word_regex):
				tables += [groups[1] for groups in re.findall(regex, query)]

			if dataent.flags.touched_tables is None:
				dataent.flags.touched_tables = set()
			dataent.flags.touched_tables.update(tables)


def enqueue_jobs_after_commit():
	if dataent.flags.enqueue_after_commit and len(dataent.flags.enqueue_after_commit) > 0:
		for job in dataent.flags.enqueue_after_commit:
			q = get_queue(job.get("queue"), is_async=job.get("is_async"))
			q.enqueue_call(execute_job, timeout=job.get("timeout"),
							kwargs=job.get("queue_args"))
		dataent.flags.enqueue_after_commit = []
