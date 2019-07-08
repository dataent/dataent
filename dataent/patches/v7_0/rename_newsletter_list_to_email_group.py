from __future__ import unicode_literals
import dataent

def execute():
	dataent.rename_doc('DocType', 'Newsletter List', 'Email Group')
	dataent.rename_doc('DocType', 'Newsletter List Subscriber', 'Email Group Member')