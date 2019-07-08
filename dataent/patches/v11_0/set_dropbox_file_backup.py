from __future__ import unicode_literals
from dataent.utils import cint
import dataent

def execute():
	dataent.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(dataent.db.get_value("Dropbox Settings", None, "enabled"))
	if  check_dropbox_enabled == 1:
		dataent.db.set_value("Dropbox Settings", None, 'file_backup', 1)
