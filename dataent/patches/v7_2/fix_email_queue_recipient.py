from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc('email', 'doctype', 'email_queue_recipient')
	dataent.db.sql('update `tabEmail Queue Recipient` set parenttype="recipients"')