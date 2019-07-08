from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "user_email")
	dataent.reload_doc("core", "doctype", "user")
	for user_name in dataent.get_all('User', filters={'user_type': 'Website User'}):
		user = dataent.get_doc('User', user_name)
		if user.roles:
			user.roles = []
			user.save()
