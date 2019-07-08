from __future__ import unicode_literals
import dataent

def execute():
	dataent.delete_doc("DocType", "Post")
	dataent.delete_doc("DocType", "Website Group")
	dataent.delete_doc("DocType", "Website Route Permission")
	dataent.delete_doc("DocType", "User Vote")
	dataent.delete_doc("DocType", "Notification Count")
