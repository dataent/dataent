from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype('DocPerm')
	if dataent.db.has_column('DocPerm', 'is_custom'):
		dataent.db.commit()
		dataent.db.sql('alter table `tabDocPerm` drop column is_custom')