# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "print_settings")
	print_settings = dataent.get_doc("Print Settings")
	print_settings.with_letterhead = 1
	print_settings.save()
