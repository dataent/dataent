# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent

def add_custom_field(doctype, fieldname, fieldtype='Data', options=None):
	dataent.get_doc({
		"doctype": "Custom Field",
		"dt": doctype,
		"fieldname": fieldname,
		"fieldtype": fieldtype,
		"options": options
	}).insert()

def clear_custom_fields(doctype):
	dataent.db.sql('delete from `tabCustom Field` where dt=%s', doctype)
	dataent.clear_cache(doctype=doctype)
