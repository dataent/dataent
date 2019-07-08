# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import dataent, json
from dataent import _dict
import dataent.share
from dataent.utils import cint
from dataent.boot import get_allowed_reports
from dataent.permissions import get_roles, get_valid_perms
from dataent.core.doctype.domain_settings.domain_settings import get_active_modules

class UserPermissions:
	"""
	A user permission object can be accessed as `dataent.get_user()`
	"""
	def __init__(self, name=''):
		self.defaults = None
		self.name = name or dataent.session.get('user')
		self.roles = []

		self.all_read = []
		self.can_create = []
		self.can_read = []
		self.can_write = []
		self.can_cancel = []
		self.can_delete = []
		self.can_search = []
		self.can_get_report = []
		self.can_import = []
		self.can_export = []
		self.can_print = []
		self.can_email = []
		self.can_set_user_permissions = []
		self.allow_modules = []
		self.in_create = []
		self.setup_user()

	def setup_user(self):
		def get_user_doc():
			user = None
			try:
				user = dataent.get_doc("User", self.name).as_dict()
			except dataent.DoesNotExistError:
				pass
			except Exception as e:
				# install boo-boo
				if e.args[0] != 1146: raise

			return user

		if not dataent.flags.in_install_db and not dataent.flags.in_test:
			user_doc = dataent.cache().hget("user_doc", self.name, get_user_doc)
			if user_doc:
				self.doc = dataent.get_doc(user_doc)

	def get_roles(self):
		"""get list of roles"""
		if not self.roles:
			self.roles = get_roles(self.name)
		return self.roles

	def build_doctype_map(self):
		"""build map of special doctype properties"""

		active_domains = dataent.get_active_domains()

		self.doctype_map = {}
		for r in dataent.db.sql("""select name, in_create, issingle, istable,
			read_only, restrict_to_domain, module from tabDocType""", as_dict=1):
			if (not r.restrict_to_domain) or (r.restrict_to_domain in active_domains):
				self.doctype_map[r['name']] = r

	def build_perm_map(self):
		"""build map of permissions at level 0"""
		self.perm_map = {}
		for r in get_valid_perms():
			dt = r['parent']

			if not dt in self.perm_map:
				self.perm_map[dt] = {}

			for k in dataent.permissions.rights:
				if not self.perm_map[dt].get(k):
					self.perm_map[dt][k] = r.get(k)

	def build_permissions(self):
		"""build lists of what the user can read / write / create
		quirks:
			read_only => Not in Search
			in_create => Not in create
		"""
		self.build_doctype_map()
		self.build_perm_map()
		user_shared = dataent.share.get_shared_doctypes()
		no_list_view_link = []
		active_modules = get_active_modules() or []
		for dt in self.doctype_map:
			dtp = self.doctype_map[dt]

			p = self.perm_map.get(dt, {})

			if not p.get("read") and (dt in user_shared):
				p["read"] = 1

			if not dtp.get('istable'):
				if p.get('create') and not dtp.get('issingle'):
					if dtp.get('in_create'):
						self.in_create.append(dt)
					else:
						self.can_create.append(dt)
				elif p.get('write'):
					self.can_write.append(dt)
				elif p.get('read'):
					if dtp.get('read_only'):
						# read_only = "User Cannot Search"
						self.all_read.append(dt)
						no_list_view_link.append(dt)
					else:
						self.can_read.append(dt)

			if p.get('cancel'):
				self.can_cancel.append(dt)

			if p.get('delete'):
				self.can_delete.append(dt)

			if (p.get('read') or p.get('write') or p.get('create')):
				if p.get('report'):
					self.can_get_report.append(dt)
				for key in ("import", "export", "print", "email", "set_user_permissions"):
					if p.get(key):
						getattr(self, "can_" + key).append(dt)

				if not dtp.get('istable'):
					if not dtp.get('issingle') and not dtp.get('read_only'):
						self.can_search.append(dt)
					if dtp.get('module') not in self.allow_modules:
						if active_modules and dtp.get('module') not in active_modules:
							pass
						else:
							self.allow_modules.append(dtp.get('module'))

		self.can_write += self.can_create
		self.can_write += self.in_create
		self.can_read += self.can_write

		self.shared = dataent.db.sql_list("""select distinct share_doctype from `tabDocShare`
			where `user`=%s and `read`=1""", self.name)
		self.can_read = list(set(self.can_read + self.shared))

		self.all_read += self.can_read

		for dt in no_list_view_link:
			if dt in self.can_read:
				self.can_read.remove(dt)

		if "System Manager" in self.get_roles():
			self.can_import = filter(lambda d: d in self.can_create,
				dataent.db.sql_list("""select name from `tabDocType` where allow_import = 1"""))

	def get_defaults(self):
		import dataent.defaults
		self.defaults = dataent.defaults.get_defaults(self.name)
		return self.defaults

	# update recent documents
	def update_recent(self, dt, dn):
		rdl = dataent.cache().hget("user_recent", self.name) or []
		new_rd = [dt, dn]

		# clear if exists
		for i in range(len(rdl)):
			rd = rdl[i]
			if rd==new_rd:
				del rdl[i]
				break

		if len(rdl) > 19:
			rdl = rdl[:19]

		rdl = [new_rd] + rdl

		dataent.cache().hset("user_recent", self.name, rdl)

	def _get(self, key):
		if not self.can_read:
			self.build_permissions()
		return getattr(self, key)

	def get_can_read(self):
		"""return list of doctypes that the user can read"""
		if not self.can_read:
			self.build_permissions()
		return self.can_read

	def load_user(self):
		d = dataent.db.sql("""select email, first_name, last_name, creation,
			email_signature, user_type, language, background_image, background_style,
			mute_sounds, send_me_a_copy from tabUser where name = %s""", (self.name,), as_dict=1)[0]

		if not self.can_read:
			self.build_permissions()

		d.name = self.name
		d.recent = json.dumps(dataent.cache().hget("user_recent", self.name) or [])

		d.roles = self.get_roles()
		d.defaults = self.get_defaults()

		for key in ("can_create", "can_write", "can_read", "can_cancel", "can_delete",
			"can_get_report", "allow_modules", "all_read", "can_search",
			"in_create", "can_export", "can_import", "can_print", "can_email",
			"can_set_user_permissions"):
			d[key] = list(set(getattr(self, key)))

		d.all_reports = self.get_all_reports()
		return d

	def get_all_reports(self):
		return get_allowed_reports()

def get_user_fullname(user):
	fullname = dataent.db.sql("SELECT CONCAT_WS(' ', first_name, last_name) FROM `tabUser` WHERE name=%s", (user,))
	return fullname and fullname[0][0] or ''

def get_fullname_and_avatar(user):
	first_name, last_name, avatar, name = dataent.db.get_value("User",
		user, ["first_name", "last_name", "user_image", "name"])
	return _dict({
		"fullname": " ".join(filter(None, [first_name, last_name])),
		"avatar": avatar,
		"name": name
	})

def get_system_managers(only_name=False):
	"""returns all system manager's user details"""
	import email.utils
	from dataent.core.doctype.user.user import STANDARD_USERS
	system_managers = dataent.db.sql("""select distinct name,
		concat_ws(" ", if(first_name="", null, first_name), if(last_name="", null, last_name))
		as fullname from tabUser p
		where docstatus < 2 and enabled = 1
		and name not in ({})
		and exists (select * from `tabHas Role` ur
			where ur.parent = p.name and ur.role="System Manager")
		order by creation desc""".format(", ".join(["%s"]*len(STANDARD_USERS))),
			STANDARD_USERS, as_dict=True)

	if only_name:
		return [p.name for p in system_managers]
	else:
		return [email.utils.formataddr((p.fullname, p.name)) for p in system_managers]

def add_role(user, role):
	dataent.get_doc("User", user).add_roles(role)

def add_system_manager(email, first_name=None, last_name=None, send_welcome_email=False, password=None):
	# add user
	user = dataent.new_doc("User")
	user.update({
		"name": email,
		"email": email,
		"enabled": 1,
		"first_name": first_name or email,
		"last_name": last_name,
		"user_type": "System User",
		"send_welcome_email": 1 if send_welcome_email else 0
	})

	user.insert()

	# add roles
	roles = dataent.db.sql_list("""select name from `tabRole`
		where name not in ("Administrator", "Guest", "All")""")
	user.add_roles(*roles)

	if password:
		from dataent.utils.password import update_password
		update_password(user=user.name, pwd=password)

def get_enabled_system_users():
	return dataent.db.sql("""select * from tabUser where
		user_type='System User' and enabled=1 and name not in ('Administrator', 'Guest')""", as_dict=1)

def is_website_user():
	return dataent.db.get_value('User', dataent.session.user, 'user_type') == "Website User"

def is_system_user(username):
	return dataent.db.get_value("User", {"name": username, "enabled": 1, "user_type": "System User"})

def get_users():
	from dataent.core.doctype.user.user import get_system_users
	users = []
	system_managers = dataent.utils.user.get_system_managers(only_name=True)
	for user in get_system_users():
		users.append({
			"full_name": dataent.utils.user.get_user_fullname(user),
			"email": user,
			"is_system_manager": 1 if (user in system_managers) else 0
		})

	return users

def set_last_active_to_now(user):
	from dataent.utils import now_datetime
	dataent.db.set_value("User", user, "last_active", now_datetime())

def disable_users(limits=None):
	if not limits:
		return

	if limits.get('users'):
		system_manager = get_system_managers(only_name=True)
		user_list = ['Administrator', 'Guest']
		if system_manager:
			user_list.append(system_manager[-1])
		#exclude system manager from active user list
		# active_users =  dataent.db.sql_list("""select name from tabUser
		# 	where name not in ('Administrator', 'Guest', %s) and user_type = 'System User' and enabled=1
		# 	order by creation desc""", system_manager)
		active_users = dataent.get_all("User", filters={"user_type":"System User", "enabled":1, "name": ["not in", user_list]}, fields=["name"])
		user_limit = cint(limits.get('users')) - 1

		if len(active_users) > user_limit:

			# if allowed user limit 1 then deactivate all additional users
			# else extract additional user from active user list and deactivate them
			if cint(limits.get('users')) != 1:
				active_users = active_users[:-1 * user_limit]

			for user in active_users:
				dataent.db.set_value("User", user, 'enabled', 0)

		from dataent.core.doctype.user.user import get_total_users

		if get_total_users() > cint(limits.get('users')):
			reset_simultaneous_sessions(cint(limits.get('users')))

	dataent.db.commit()

def reset_simultaneous_sessions(user_limit):
	for user in dataent.db.sql("""select name, simultaneous_sessions from tabUser
		where name not in ('Administrator', 'Guest') and user_type = 'System User' and enabled=1
		order by creation desc""", as_dict=1):
		if user.simultaneous_sessions < user_limit:
			user_limit = user_limit - user.simultaneous_sessions
		else:
			dataent.db.set_value("User", user.name, "simultaneous_sessions", 1)
			user_limit = user_limit - 1

def get_link_to_reset_password(user):
	link = ''

	if not cint(dataent.db.get_single_value('System Settings', 'setup_complete')):
		user = dataent.get_doc("User", user)
		link = user.reset_password(send_email=False)
		dataent.db.commit()

	return {
		'link': link
	}
