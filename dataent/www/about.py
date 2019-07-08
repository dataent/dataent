# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def get_context(context):
	context.doc = dataent.get_doc("About Us Settings", "About Us Settings")

	context.parents = [
		{ "name": dataent._("Home"), "route": "/" }
	]

	return context
