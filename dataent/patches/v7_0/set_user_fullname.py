from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("Core", "DocType", "User")
	
	for user in dataent.db.get_all('User'):
		user = dataent.get_doc('User', user.name)
		user.set_full_name()
		user.db_set('full_name', user.full_name, update_modified = False)