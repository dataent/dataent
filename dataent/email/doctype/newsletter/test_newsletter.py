# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

import dataent, unittest

from dataent.email.doctype.newsletter.newsletter import confirmed_unsubscribe
from six.moves.urllib.parse import unquote


emails = ["test_subscriber1@example.com", "test_subscriber2@example.com",
			"test_subscriber3@example.com", "test1@example.com"]

class TestNewsletter(unittest.TestCase):
	def setUp(self):
		dataent.set_user("Administrator")
		dataent.db.sql('delete from `tabEmail Group Member`')
		for email in emails:
				dataent.get_doc({
					"doctype": "Email Group Member",
					"email": email,
					"email_group": "_Test Email Group"
				}).insert()

	def test_send(self):
		name = self.send_newsletter()

		email_queue_list = [dataent.get_doc('Email Queue', e.name) for e in dataent.get_all("Email Queue")]
		self.assertEqual(len(email_queue_list), 4)
		recipients = [e.recipients[0].recipient for e in email_queue_list]
		for email in emails:
			self.assertTrue(email in recipients)

	def test_unsubscribe(self):
		# test unsubscribe
		name = self.send_newsletter()
		from dataent.email.queue import flush
		flush(from_test=True)
		to_unsubscribe = unquote(dataent.local.flags.signed_query_string.split("email=")[1].split("&")[0])

		confirmed_unsubscribe(to_unsubscribe, name)

		name = self.send_newsletter()

		email_queue_list = [dataent.get_doc('Email Queue', e.name) for e in dataent.get_all("Email Queue")]
		self.assertEqual(len(email_queue_list), 3)
		recipients = [e.recipients[0].recipient for e in email_queue_list]
		for email in emails:
			if email != to_unsubscribe:
				self.assertTrue(email in recipients)

	@staticmethod
	def send_newsletter(published=0):
		dataent.db.sql("delete from `tabEmail Queue`")
		dataent.db.sql("delete from `tabEmail Queue Recipient`")
		dataent.db.sql("delete from `tabNewsletter`")
		newsletter = dataent.get_doc({
			"doctype": "Newsletter",
			"subject": "_Test Newsletter",
			"send_from": "Test Sender <test_sender@example.com>",
			"message": "Testing my news.",
			"published": published
		}).insert(ignore_permissions=True)

		newsletter.append("email_group", {"email_group": "_Test Email Group"})
		newsletter.save()
		newsletter.send_emails()
		return newsletter.name

	def test_portal(self):
		self.send_newsletter(1)
		dataent.set_user("test1@example.com")
		from dataent.email.doctype.newsletter.newsletter import get_newsletter_list
		newsletters = get_newsletter_list("Newsletter", None, None, 0)
		self.assertEqual(len(newsletters), 1)

	def test_newsletter_context(self):
		context = dataent._dict()
		newsletter_name = self.send_newsletter(1)
		dataent.set_user("test2@example.com")
		doc = dataent.get_doc("Newsletter", newsletter_name)
		doc.get_context(context)
		self.assertEqual(context.no_cache, 1)
		self.assertTrue("attachments" not in list(context))


test_dependencies = ["Email Group"]
