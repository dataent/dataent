# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	for doctype in dataent.db.sql_list("""select name from `tabDocType` where istable=1"""):
		dataent.db.sql("""delete from `tab{0}` where parent like "old_par%:%" """.format(doctype))
	dataent.db.sql("""delete from `tabDocField` where parent="0" """)
