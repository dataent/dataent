# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals
import dataent
import dataent.share
import unittest

class TestDocShare(unittest.TestCase):
	def setUp(self):
		self.user = "test@example.com"
		self.event = dataent.get_doc({"doctype": "Event",
			"subject": "test share event",
			"starts_on": "2015-01-01 10:00:00",
			"event_type": "Private"}).insert()

	def tearDown(self):
		dataent.set_user("Administrator")
		self.event.delete()

	def test_add(self):
		# user not shared
		self.assertTrue(self.event.name not in dataent.share.get_shared("Event", self.user))
		dataent.share.add("Event", self.event.name, self.user)
		self.assertTrue(self.event.name in dataent.share.get_shared("Event", self.user))

	def test_doc_permission(self):
		dataent.set_user(self.user)
		self.assertFalse(self.event.has_permission())

		dataent.set_user("Administrator")
		dataent.share.add("Event", self.event.name, self.user)

		dataent.set_user(self.user)
		self.assertTrue(self.event.has_permission())

	def test_share_permission(self):
		dataent.share.add("Event", self.event.name, self.user, write=1, share=1)

		dataent.set_user(self.user)
		self.assertTrue(self.event.has_permission("share"))

		# test cascade
		self.assertTrue(self.event.has_permission("read"))
		self.assertTrue(self.event.has_permission("write"))

	def test_set_permission(self):
		dataent.share.add("Event", self.event.name, self.user)

		dataent.set_user(self.user)
		self.assertFalse(self.event.has_permission("share"))

		dataent.set_user("Administrator")
		dataent.share.set_permission("Event", self.event.name, self.user, "share")

		dataent.set_user(self.user)
		self.assertTrue(self.event.has_permission("share"))

	def test_permission_to_share(self):
		dataent.set_user(self.user)
		self.assertRaises(dataent.PermissionError, dataent.share.add, "Event", self.event.name, self.user)

		dataent.set_user("Administrator")
		dataent.share.add("Event", self.event.name, self.user, write=1, share=1)

		# test not raises
		dataent.set_user(self.user)
		dataent.share.add("Event", self.event.name, "test1@example.com", write=1, share=1)

	def test_remove_share(self):
		dataent.share.add("Event", self.event.name, self.user, write=1, share=1)

		dataent.set_user(self.user)
		self.assertTrue(self.event.has_permission("share"))

		dataent.set_user("Administrator")
		dataent.share.remove("Event", self.event.name, self.user)

		dataent.set_user(self.user)
		self.assertFalse(self.event.has_permission("share"))

	def test_share_with_everyone(self):
		self.assertTrue(self.event.name not in dataent.share.get_shared("Event", self.user))

		dataent.share.set_permission("Event", self.event.name, None, "read", everyone=1)
		self.assertTrue(self.event.name in dataent.share.get_shared("Event", self.user))
		self.assertTrue(self.event.name in dataent.share.get_shared("Event", "test1@example.com"))
		self.assertTrue(self.event.name not in dataent.share.get_shared("Event", "Guest"))

		dataent.share.set_permission("Event", self.event.name, None, "read", value=0, everyone=1)
		self.assertTrue(self.event.name not in dataent.share.get_shared("Event", self.user))
		self.assertTrue(self.event.name not in dataent.share.get_shared("Event", "test1@example.com"))
		self.assertTrue(self.event.name not in dataent.share.get_shared("Event", "Guest"))
