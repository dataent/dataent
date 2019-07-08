# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	user_owner = dataent.db.get_value("Custom Field", {"fieldname": "user_owner"})
	if user_owner:
		dataent.delete_doc("Custom Field", user_owner)
