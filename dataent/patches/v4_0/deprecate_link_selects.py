# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	for name in dataent.db.sql_list("""select name from `tabCustom Field`
		where fieldtype="Select" and options like "link:%" """):
		custom_field = dataent.get_doc("Custom Field", name)
		custom_field.fieldtype = "Link"
		custom_field.options = custom_field.options[5:]
		custom_field.save()
