from __future__ import unicode_literals
import dataent
from dataent.permissions import reset_perms

def execute():
	dataent.reload_doctype("Communication")

	# set status = "Linked"
	dataent.db.sql("""update `tabCommunication` set status='Linked'
		where ifnull(reference_doctype, '')!='' and ifnull(reference_name, '')!=''""")

	dataent.db.sql("""update `tabCommunication` set status='Closed'
		where status='Archived'""")

	# reset permissions if owner of all DocPerms is Administrator
	if not dataent.db.sql("""select name from `tabDocPerm`
		where parent='Communication' and ifnull(owner, '')!='Administrator'"""):

		reset_perms("Communication")
