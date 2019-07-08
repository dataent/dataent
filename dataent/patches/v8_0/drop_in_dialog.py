from __future__ import unicode_literals
import dataent

def execute():
	if dataent.db.has_column('DocType', 'in_dialog'):
		dataent.db.sql('alter table tabDocType drop column in_dialog')
	dataent.clear_cache(doctype="DocType")