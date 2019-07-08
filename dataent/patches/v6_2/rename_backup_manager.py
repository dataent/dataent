from __future__ import unicode_literals
import dataent

def execute():
	unset = False
	dataent.reload_doc("integrations", "doctype", "dropbox_backup")

	dropbox_backup = dataent.get_doc("Dropbox Backup", "Dropbox Backup")
	for df in dropbox_backup.meta.fields:
		value = dataent.db.get_single_value("Backup Manager", df.fieldname)
		if value:
			if df.fieldname=="upload_backups_to_dropbox" and value=="Never":
				value = "Daily"
				unset = True
			dropbox_backup.set(df.fieldname, value)

	if unset:
		dropbox_backup.set("send_backups_to_dropbox", 0)

	dropbox_backup.save()
