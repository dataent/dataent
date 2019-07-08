from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype('System Settings')
	last = dataent.db.get_global('scheduler_last_event')
	dataent.db.set_value('System Settings', 'System Settings', 'scheduler_last_event', last)

