from __future__ import unicode_literals
import dataent

def execute():
	if dataent.db.has_column('DocField', 'in_filter'):
		dataent.db.sql('alter table tabDocField drop column in_filter')
	dataent.clear_cache(doctype="DocField")