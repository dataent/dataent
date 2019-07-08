from __future__ import unicode_literals
import dataent
import dataent.share

def execute():
	dataent.reload_doc("core", "doctype", "docperm")
	dataent.reload_doc("core", "doctype", "docshare")
	dataent.reload_doc('email', 'doctype', 'email_account')

	# default share to all writes
	dataent.db.sql("""update tabDocPerm set `share`=1 where ifnull(`write`,0)=1 and ifnull(`permlevel`,0)=0""")

	# every user must have access to his / her own detail
	users = dataent.get_all("User", filters={"user_type": "System User"})
	usernames = [user.name for user in users]
	for user in usernames:
		dataent.share.add("User", user, user, write=1, share=1)

	# move event user to shared
	if dataent.db.exists("DocType", "Event User"):
		for event in dataent.get_all("Event User", fields=["parent", "person"]):
			if event.person in usernames:
				if not dataent.db.exists("Event", event.parent):
					dataent.db.sql("delete from `tabEvent User` where parent = %s",event.parent)
				else:
					dataent.share.add("Event", event.parent, event.person, write=1)

		dataent.delete_doc("DocType", "Event User")

	# move note user to shared
	if dataent.db.exists("DocType", "Note User"):
		for note in dataent.get_all("Note User", fields=["parent", "user", "permission"]):
			perm = {"read": 1} if note.permission=="Read" else {"write": 1}
			if note.user in usernames:
				dataent.share.add("Note", note.parent, note.user, **perm)

		dataent.delete_doc("DocType", "Note User")
