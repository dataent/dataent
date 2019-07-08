# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals

import dataent
no_cache = True

def get_context(context):
	token   = dataent.local.form_dict.token
	doc     = dataent.get_doc(dataent.local.form_dict.doctype, dataent.local.form_dict.docname)

	context.payment_message = ''
	if hasattr(doc, 'get_payment_success_message'):
		context.payment_message = doc.get_payment_success_message()

