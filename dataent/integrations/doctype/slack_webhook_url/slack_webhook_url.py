# -*- coding: utf-8 -*-
# Copyright (c) 2018, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent.utils import get_url_to_form
from dataent import _
import requests
import json

class SlackWebhookURL(Document):
	pass

def send_slack_message(webhook_url, message, reference_doctype, reference_name):
	slack_url = dataent.db.get_value("Slack Webhook URL", webhook_url, "webhook_url")
	doc_url = get_url_to_form(reference_doctype, reference_name)
	attachments = [
		{
			"fallback": _("See the document at {0}").format(doc_url),
			"actions": [
				{
				"type": "button",
				"text": _("Go to the document"),
				"url": doc_url,
				"style": "primary"
				}
			]
		}
	]
	data = {"text": message, "attachments": attachments}
	r = requests.post(slack_url, data=json.dumps(data))


	if r.ok == True:
		return 'success'

	elif r.ok == False:
		dataent.log_error(r.error, _('Slack Webhook Error'))
		return 'error'
