# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent, unittest, json

class TestSeen(unittest.TestCase):
	def tearDown(self):
		dataent.set_user('Administrator')

	def test_if_user_is_added(self):
		ev = dataent.get_doc({
			'doctype': 'Event',
			'subject': 'test event for seen',
			'starts_on': '2016-01-01 10:10:00',
			'event_type': 'Public'
		}).insert()

		dataent.set_user('test@example.com')

		from dataent.desk.form.load import getdoc

		# load the form
		getdoc('Event', ev.name)

		# reload the event
		ev = dataent.get_doc('Event', ev.name)

		self.assertTrue('test@example.com' in json.loads(ev._seen))

		# test another user
		dataent.set_user('test1@example.com')

		# load the form
		getdoc('Event', ev.name)

		# reload the event
		ev = dataent.get_doc('Event', ev.name)

		self.assertTrue('test@example.com' in json.loads(ev._seen))
		self.assertTrue('test1@example.com' in json.loads(ev._seen))

		ev.save()

		self.assertFalse('test@example.com' in json.loads(ev._seen))
		self.assertTrue('test1@example.com' in json.loads(ev._seen))
