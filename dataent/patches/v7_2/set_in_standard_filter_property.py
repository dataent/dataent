from __future__ import unicode_literals
import dataent
import pymysql

def execute():
	dataent.reload_doc('custom', 'doctype', 'custom_field', force=True)

	try:
		dataent.db.sql('update `tabCustom Field` set in_standard_filter = in_filter_dash')
	except Exception as e:
		if e.args[0]!=1054: raise e

	for doctype in dataent.get_all("DocType", {"istable": 0, "issingle": 0, "custom": 0}):
		try:
			dataent.reload_doctype(doctype.name, force=True)
		except KeyError:
			pass
		except pymysql.err.DataError:
			pass
