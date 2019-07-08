# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	try:
		dataent.db.sql("alter table `tabEmail Queue` change `ref_docname` `reference_name` varchar(255)")
	except Exception as e:
		if e.args[0] not in (1054, 1060):
			raise

	try:
		dataent.db.sql("alter table `tabEmail Queue` change `ref_doctype` `reference_doctype` varchar(255)")
	except Exception as e:
		if e.args[0] not in (1054, 1060):
			raise
	dataent.reload_doctype("Email Queue")
