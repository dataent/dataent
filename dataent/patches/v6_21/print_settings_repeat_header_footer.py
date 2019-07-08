from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype('Print Settings')
	dataent.db.set_value('Print Settings', 'Print Settings', 'repeat_header_footer', 1)
