from __future__ import unicode_literals
import dataent

def execute():
	dataent.db.set_value("Print Settings", "Print Settings", "allow_print_for_draft", 1)