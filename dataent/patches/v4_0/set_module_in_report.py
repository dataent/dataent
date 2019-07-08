# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "report")
	dataent.db.sql("""update `tabReport` r set r.module=(select d.module from `tabDocType` d
		where d.name=r.ref_doctype) where ifnull(r.module, '')=''""")