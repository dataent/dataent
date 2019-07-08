from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "todo")
	try:
		dataent.db.sql("""update tabToDo set status = if(ifnull(checked,0)=0, 'Open', 'Closed')""")
	except:
		pass
