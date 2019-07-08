# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest

class TestWebhook(unittest.TestCase):
	def test_validate_docevents(self):
		doc = dataent.new_doc("Webhook")
		doc.webhook_doctype = "User"
		doc.webhook_docevent = "on_submit"
		doc.request_url = "https://httpbin.org/post"
		self.assertRaises(dataent.ValidationError, doc.save)
	def test_validate_request_url(self):
		doc = dataent.new_doc("Webhook")
		doc.webhook_doctype = "User"
		doc.webhook_docevent = "after_insert"
		doc.request_url = "httpbin.org?post"
		self.assertRaises(dataent.ValidationError, doc.save)
