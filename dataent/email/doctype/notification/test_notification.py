# -*- coding: utf-8 -*-
# Copyright (c) 2018, Dataent Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent, dataent.utils, dataent.utils.scheduler
import unittest

test_records = dataent.get_test_records('Notification')

test_dependencies = ["User"]

class TestNotification(unittest.TestCase):
	def setUp(self):
		dataent.db.sql("""delete from `tabEmail Queue`""")
		dataent.set_user("test1@example.com")

	def tearDown(self):
		dataent.set_user("Administrator")

	def test_new_and_save(self):
		communication = dataent.new_doc("Communication")
		communication.communication_type = 'Comment'
		communication.subject = "test"
		communication.content = "test"
		communication.insert(ignore_permissions=True)

		self.assertTrue(dataent.db.get_value("Email Queue", {"reference_doctype": "Communication",
			"reference_name": communication.name, "status":"Not Sent"}))
		dataent.db.sql("""delete from `tabEmail Queue`""")

		communication.content = "test 2"
		communication.save()

		self.assertTrue(dataent.db.get_value("Email Queue", {"reference_doctype": "Communication",
			"reference_name": communication.name, "status":"Not Sent"}))

		self.assertEqual(dataent.db.get_value('Communication',
			communication.name, 'subject'), '__testing__')

	def test_condition(self):
		event = dataent.new_doc("Event")
		event.subject = "test",
		event.event_type = "Private"
		event.starts_on  = "2014-06-06 12:00:00"
		event.insert()

		self.assertFalse(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status":"Not Sent"}))

		event.event_type = "Public"
		event.save()

		self.assertTrue(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status":"Not Sent"}))

	def test_invalid_condition(self):
		dataent.set_user("Administrator")
		notification = dataent.new_doc("Notification")
		notification.subject = "test"
		notification.document_type = "ToDo"
		notification.send_alert_on = "New"
		notification.message = "test"

		recipent = dataent.new_doc("Notification Recipient")
		recipent.email_by_document_field = "owner"

		notification.recipents = recipent
		notification.condition = "test"

		self.assertRaises(dataent.ValidationError, notification.save)
		notification.delete()


	def test_value_changed(self):
		event = dataent.new_doc("Event")
		event.subject = "test",
		event.event_type = "Private"
		event.starts_on  = "2014-06-06 12:00:00"
		event.insert()

		self.assertFalse(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status":"Not Sent"}))

		event.subject = "test 1"
		event.save()

		self.assertFalse(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status":"Not Sent"}))

		event.description = "test"
		event.save()

		self.assertTrue(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status":"Not Sent"}))

	def test_alert_disabled_on_wrong_field(self):
		dataent.set_user('Administrator')
		notification = dataent.get_doc({
			"doctype": "Notification",
			"subject":"_Test Notification for wrong field",
			"document_type": "Event",
			"event": "Value Change",
			"attach_print": 0,
			"value_changed": "description1",
			"message": "Description changed",
			"recipients": [
				{ "email_by_document_field": "owner" }
			]
		}).insert()

		event = dataent.new_doc("Event")
		event.subject = "test-2",
		event.event_type = "Private"
		event.starts_on  = "2014-06-06 12:00:00"
		event.insert()
		event.subject = "test 1"
		event.save()

		# verify that notification is disabled
		notification.reload()
		self.assertEqual(notification.enabled, 0)
		notification.delete()
		event.delete()

	def test_date_changed(self):

		event = dataent.new_doc("Event")
		event.subject = "test",
		event.event_type = "Private"
		event.starts_on = "2014-01-01 12:00:00"
		event.insert()

		self.assertFalse(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status": "Not Sent"}))

		dataent.set_user('Administrator')
		dataent.utils.scheduler.trigger(dataent.local.site, "daily", now=True)

		# not today, so no alert
		self.assertFalse(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status": "Not Sent"}))

		event.starts_on  = dataent.utils.add_days(dataent.utils.nowdate(), 2) + " 12:00:00"
		event.save()

		# Value Change notification alert will be trigger as description is not changed
		# mail will not be sent
		self.assertFalse(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status": "Not Sent"}))

		dataent.utils.scheduler.trigger(dataent.local.site, "daily", now=True)

		# today so show alert
		self.assertTrue(dataent.db.get_value("Email Queue", {"reference_doctype": "Event",
			"reference_name": event.name, "status":"Not Sent"}))

	def test_cc_jinja(self):

		dataent.db.sql("""delete from `tabUser` where email='test_jinja@example.com'""")
		dataent.db.sql("""delete from `tabEmail Queue`""")
		dataent.db.sql("""delete from `tabEmail Queue Recipient`""")

		test_user = dataent.new_doc("User")
		test_user.name = 'test_jinja'
		test_user.first_name = 'test_jinja'
		test_user.email = 'test_jinja@example.com'

		test_user.insert(ignore_permissions=True)

		self.assertTrue(dataent.db.get_value("Email Queue", {"reference_doctype": "User",
			"reference_name": test_user.name, "status":"Not Sent"}))

		self.assertTrue(dataent.db.get_value("Email Queue Recipient", {"recipient": "test_jinja@example.com"}))

		dataent.db.sql("""delete from `tabUser` where email='test_jinja@example.com'""")
		dataent.db.sql("""delete from `tabEmail Queue`""")
		dataent.db.sql("""delete from `tabEmail Queue Recipient`""")
