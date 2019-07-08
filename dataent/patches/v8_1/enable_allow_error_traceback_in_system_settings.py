# Copyright (c) 2017, Dataent and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	""" enable the allow_enable_traceback property in system settings """

	dataent.reload_doc("core", "doctype", "system_settings")
	doc = dataent.get_doc("System Settings", "System Settings")
	doc.allow_error_traceback = 1
	doc.flags.ignore_permissions=True
	doc.flags.ignore_mandatory=True
	doc.save()