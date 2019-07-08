# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "system_settings")
	dataent.db.set_value('System Settings', None, "allow_login_after_fail", 60)