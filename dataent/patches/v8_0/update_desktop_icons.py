# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.utils import cstr

def execute():
	""" update the desktop icons """

	dataent.reload_doc('desk', 'doctype', 'desktop_icon')

	icons = dataent.get_all("Desktop Icon", filters={ "type": "link" }, fields=["link", "name"])

	for icon in icons:
		# check if report exists
		icon_link = icon.get("link", "") or ""
		parts = icon_link.split("/")
		if not parts:
			continue

		report_name = parts[-1]
		if "report" in parts[0] and dataent.db.get_value("Report", report_name):
			dataent.db.sql(""" update `tabDesktop Icon` set _report='{report_name}'
				where name='{name}'""".format(report_name=report_name, name=icon.get("name")))