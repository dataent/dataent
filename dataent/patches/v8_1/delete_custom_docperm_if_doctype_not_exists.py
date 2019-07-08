from __future__ import unicode_literals
import dataent

def execute():
	dataent.db.sql("""delete from `tabCustom DocPerm`
		where parent not in ( select name from `tabDocType` )
	""")
