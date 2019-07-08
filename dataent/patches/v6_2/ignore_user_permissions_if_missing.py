from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype("System Settings")
	system_settings = dataent.get_doc("System Settings")
	system_settings.flags.ignore_mandatory = 1
	system_settings.save()
