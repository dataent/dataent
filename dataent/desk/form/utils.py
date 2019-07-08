# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent, json
import dataent.desk.form.meta
import dataent.desk.form.load
from dataent.utils.html_utils import clean_email_html

from dataent import _
from six import string_types

@dataent.whitelist()
def remove_attach():
	"""remove attachment"""
	import dataent.utils.file_manager
	fid = dataent.form_dict.get('fid')
	return dataent.utils.file_manager.remove_file(fid)

@dataent.whitelist()
def validate_link():
	"""validate link when updated by user"""
	import dataent
	import dataent.utils

	value, options, fetch = dataent.form_dict.get('value'), dataent.form_dict.get('options'), dataent.form_dict.get('fetch')

	# no options, don't validate
	if not options or options=='null' or options=='undefined':
		dataent.response['message'] = 'Ok'
		return

	valid_value = dataent.db.sql("select name from `tab%s` where name=%s" % (dataent.db.escape(options),
		'%s'), (value,))

	if valid_value:
		valid_value = valid_value[0][0]

		# get fetch values
		if fetch:
			# escape with "`"
			fetch = ", ".join(("`{0}`".format(dataent.db.escape(f.strip())) for f in fetch.split(",")))
			fetch_value = None
			try:
				fetch_value = dataent.db.sql("select %s from `tab%s` where name=%s"
					% (fetch, dataent.db.escape(options), '%s'), (value,))[0]
			except Exception as e:
				error_message = str(e).split("Unknown column '")
				fieldname = None if len(error_message)<=1 else error_message[1].split("'")[0]
				dataent.msgprint(_("Wrong fieldname <b>{0}</b> in add_fetch configuration of custom script").format(fieldname))
				dataent.errprint(dataent.get_traceback())

			if fetch_value:
				dataent.response['fetch_values'] = [dataent.utils.parse_val(c) for c in fetch_value]

		dataent.response['valid_value'] = valid_value
		dataent.response['message'] = 'Ok'

@dataent.whitelist()
def add_comment(doc):
	"""allow any logged user to post a comment"""
	doc = dataent.get_doc(json.loads(doc))

	doc.content = clean_email_html(doc.content)

	if not (doc.doctype=="Communication" and doc.communication_type=='Comment'):
		dataent.throw(_("This method can only be used to create a Comment"), dataent.PermissionError)

	doc.insert(ignore_permissions=True)

	return doc.as_dict()

@dataent.whitelist()
def update_comment(name, content):
	"""allow only owner to update comment"""
	doc = dataent.get_doc('Communication', name)

	if dataent.session.user not in ['Administrator', doc.owner]:
		dataent.throw(_('Comment can only be edited by the owner'), dataent.PermissionError)

	doc.content = content
	doc.save(ignore_permissions=True)

@dataent.whitelist()
def get_next(doctype, value, prev, filters=None, order_by="modified desc"):

	prev = not int(prev)
	sort_field, sort_order = order_by.split(" ")

	if not filters: filters = []
	if isinstance(filters, string_types):
		filters = json.loads(filters)

	# condition based on sort order
	condition = ">" if sort_order.lower()=="desc" else "<"

	# switch the condition
	if prev:
		condition = "<" if condition==">" else "<"
	else:
		sort_order = "asc" if sort_order.lower()=="desc" else "desc"

	# add condition for next or prev item
	if not order_by[0] in [f[1] for f in filters]:
		filters.append([doctype, sort_field, condition, value])

	res = dataent.get_list(doctype,
		fields = ["name"],
		filters = filters,
		order_by = sort_field + " " + sort_order,
		limit_start=0, limit_page_length=1, as_list=True)

	if not res:
		dataent.msgprint(_("No further records"))
		return None
	else:
		return res[0][0]

def get_pdf_link(doctype, docname, print_format='Standard', no_letterhead=0):
	return '/api/method/dataent.utils.print_format.download_pdf?doctype={doctype}&name={docname}&format={print_format}&no_letterhead={no_letterhead}'.format(
		doctype = doctype,
		docname = docname,
		print_format = print_format,
		no_letterhead = no_letterhead
	)