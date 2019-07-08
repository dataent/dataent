# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.db.sql("update `tabDefaultValue` set parenttype='__default' where parenttype='Control Panel'")
	dataent.db.sql("update `tabDefaultValue` set parent='__default' where parent='Control Panel'")
	dataent.clear_cache()
