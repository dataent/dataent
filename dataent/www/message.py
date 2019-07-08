# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

from dataent.utils import strip_html_tags

no_cache = 1
no_sitemap = 1

def get_context(context):
	message_context = {}
	if hasattr(dataent.local, "message"):
		message_context["header"] = dataent.local.message_title
		message_context["title"] = strip_html_tags(dataent.local.message_title)
		message_context["message"] = dataent.local.message
		if hasattr(dataent.local, "message_success"):
			message_context["success"] = dataent.local.message_success

	elif dataent.local.form_dict.id:
		message_id = dataent.local.form_dict.id
		key = "message_id:{0}".format(message_id)
		message = dataent.cache().get_value(key, expires=True)
		if message:
			message_context.update(message.get('context', {}))
			if message.get('http_status_code'):
				dataent.local.response['http_status_code'] = message['http_status_code']

	return message_context
