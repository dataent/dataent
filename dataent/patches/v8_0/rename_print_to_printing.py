from __future__ import unicode_literals
import dataent

def execute():
	if dataent.db.exists('Module Def', 'Print'):
		dataent.reload_doc('printing', 'doctype', 'print_format')
		dataent.reload_doc('printing', 'doctype', 'print_settings')
		dataent.reload_doc('printing', 'doctype', 'print_heading')
		dataent.reload_doc('printing', 'doctype', 'letter_head')
		dataent.reload_doc('printing', 'page', 'print_format_builder')
		dataent.db.sql("""update `tabPrint Format` set module='Printing' where module='Print'""")
		
		dataent.delete_doc('Module Def', 'Print')