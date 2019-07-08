from __future__ import unicode_literals
import dataent
from dataent.model.rename_doc import rename_doc

def execute():
	if dataent.db.table_exists("Standard Reply") and not dataent.db.table_exists("Email Template"):
		rename_doc('DocType', 'Standard Reply', 'Email Template')
		dataent.reload_doc('email', 'doctype', 'email_template')
