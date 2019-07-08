# Copyright (c) 2018, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	signatures = dataent.db.get_list('User', {'email_signature': ['!=', '']},['name', 'email_signature'])
	dataent.reload_doc('core', 'doctype', 'user')
	for d in signatures:
		signature = d.get('email_signature')
		signature = signature.replace('\n', '<br>')
		signature = '<div>' + signature + '</div>'
		dataent.db.set_value('User', d.get('name'), 'email_signature', signature)