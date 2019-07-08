# Copyright (c) 2017, Dataent and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	""" change the XLS option as XLSX in the auto email report """

	dataent.reload_doc("email", "doctype", "auto_email_report")

	auto_email_list = dataent.get_all("Auto Email Report", filters={"format": "XLS"})
	for auto_email in auto_email_list:
		dataent.db.set_value("Auto Email Report", auto_email.name, "format", "XLSX")
