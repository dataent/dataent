# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest, json

from dataent.website.render import build_page
from dataent.website.doctype.web_form.web_form import accept

test_records = dataent.get_test_records('Web Form')

class TestWebForm(unittest.TestCase):
	def setUp(self):
		dataent.conf.disable_website_cache = True
		dataent.local.path = None

	def tearDown(self):
		dataent.conf.disable_website_cache = False
		dataent.local.path = None

	def test_basic(self):
		dataent.set_user("Guest")
		html = build_page("manage-events")
		self.assertTrue('<div class="login-required">' in html)

	def test_logged_in(self):
		dataent.set_user("Administrator")
		html = build_page("manage-events")
		self.assertFalse('<div class="login-required">' in html)
		self.assertTrue('"/manage-events?new=1"' in html)

	def test_accept(self):
		dataent.set_user("Administrator")
		accept(web_form='manage-events', data=json.dumps({
			'doctype': 'Event',
			'subject': '_Test Event Web Form',
			'description': '_Test Event Description',
			'starts_on': '2014-09-09'
		}))

		self.event_name = dataent.db.get_value("Event",
			{"subject": "_Test Event Web Form"})
		self.assertTrue(self.event_name)

	def test_edit(self):
		self.test_accept()
		doc={
			'doctype': 'Event',
			'subject': '_Test Event Web Form',
			'description': '_Test Event Description 1',
			'starts_on': '2014-09-09',
			'name': self.event_name
		}

		self.assertNotEquals(dataent.db.get_value("Event",
			self.event_name, "description"), doc.get('description'))

		accept(web_form='manage-events', data=json.dumps(doc))

		self.assertEqual(dataent.db.get_value("Event",
			self.event_name, "description"), doc.get('description'))
