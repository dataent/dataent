from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype("Error Log")

	from dataent.core.doctype.error_log.error_log import set_old_logs_as_seen
	set_old_logs_as_seen()
