from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype("User")
	dataent.db.sql("update `tabUser` set last_active=last_login")
