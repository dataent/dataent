from __future__ import unicode_literals
import dataent

def execute():
	column = 'apply_user_permissions'
	to_remove = ['DocPerm', 'Custom DocPerm']

	for doctype in to_remove:
		if column in dataent.db.get_table_columns(doctype):
			dataent.db.sql("alter table `tab{0}` drop column {1}".format(doctype, column))

	dataent.reload_doc('core', 'doctype', 'docperm', force=True)
	dataent.reload_doc('core', 'doctype', 'custom_docperm', force=True)

