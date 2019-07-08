from __future__ import unicode_literals
import dataent

def execute():
	if dataent.db.table_exists('Prepared Report'):
		prepared_reports = dataent.get_all("Prepared Report")
		for report in prepared_reports:
			dataent.delete_doc("Prepared Report", report.name)
