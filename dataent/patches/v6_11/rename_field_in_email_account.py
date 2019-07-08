from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("email", "doctype", "email_account")
	if dataent.db.has_column('Email Account', 'pop3_server'):
		dataent.db.sql("update `tabEmail Account` set email_server = pop3_server")
