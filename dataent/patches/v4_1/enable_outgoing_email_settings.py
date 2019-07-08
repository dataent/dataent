# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "outgoing_email_settings")
	if (dataent.db.get_value("Outgoing Email Settings", "Outgoing Email Settings", "mail_server") or "").strip():
		dataent.db.set_value("Outgoing Email Settings", "Outgoing Email Settings", "enabled", 1)
