# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	for report in dataent.db.sql_list(""" select name from `tabReport` where report_type = 'Report Builder'
		and is_standard = 'No' and `json` != '' and `json` is not null """):
		doc = dataent.get_doc("Report", report)
		doc.update_report_json()
		doc.db_set("json", doc.json, update_modified=False)