from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "communication")
	dataent.db.sql("""update tabCommunication set reference_doctype = parenttype, reference_name = parent""")
