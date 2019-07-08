from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype("User")

	# give preference to System Users
	users = dataent.db.sql_list("""select name from `tabUser` order by if(user_type='System User', 0, 1)""")
	for name in users:
		user = dataent.get_doc("User", name)
		if user.username or not user.first_name:
			continue

		username = user.suggest_username()
		if username:
			user.db_set("username", username, update_modified=False)
