from __future__ import unicode_literals
import dataent

def execute():
	for name in dataent.db.sql_list("""select name from `tabToDo`
		where ifnull(reference_type, '')!='' and ifnull(reference_name, '')!=''"""):
		try:
			dataent.get_doc("ToDo", name).on_update()
		except Exception as e:
			if e.args[0]!=1146:
				raise
