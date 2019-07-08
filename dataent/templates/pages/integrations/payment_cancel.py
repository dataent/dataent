# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals
import dataent

def get_context(context):
	token = dataent.local.form_dict.token

	if token:
		dataent.db.set_value("Integration Request", token, "status", "Cancelled")
		dataent.db.commit()
