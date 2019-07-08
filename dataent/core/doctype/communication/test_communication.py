# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest
test_records = dataent.get_test_records('Communication')


class TestCommunication(unittest.TestCase):

	def test_email(self):
		valid_email_list = ["Full Name <full@example.com>",
		'"Full Name with quotes and <weird@chars.com>" <weird@example.com>',
		"Surname, Name <name.surname@domain.com>",
		"Purchase@ABC <purchase@abc.com>", "xyz@abc2.com <xyz@abc.com>",
		"Name [something else] <name@domain.com>"]

		invalid_email_list = ["[invalid!email]", "invalid-email",
		"tes2", "e", "rrrrrrrr", "manas","[[[sample]]]",
		"[invalid!email].com"]

		for x in valid_email_list:
			self.assertTrue(dataent.utils.parse_addr(x)[1])

		for x in invalid_email_list:
			self.assertFalse(dataent.utils.parse_addr(x)[0])

	def test_name(self):
		valid_email_list = ["Full Name <full@example.com>",
		'"Full Name with quotes and <weird@chars.com>" <weird@example.com>',
		"Surname, Name <name.surname@domain.com>",
		"Purchase@ABC <purchase@abc.com>", "xyz@abc2.com <xyz@abc.com>",
		"Name [something else] <name@domain.com>"]

		invalid_email_list = ["[invalid!email]", "invalid-email",
		"tes2", "e", "rrrrrrrr", "manas","[[[sample]]]",
		"[invalid!email].com"]

		for x in valid_email_list:
			self.assertTrue(dataent.utils.parse_addr(x)[0])

		for x in invalid_email_list:
			self.assertFalse(dataent.utils.parse_addr(x)[0])

	def test_circular_linking(self):
		content = "This was created to test circular linking"
		a = dataent.get_doc({
			"doctype": "Communication",
			"communication_type": "Communication",
			"content": content,
		}).insert()
		b = dataent.get_doc({
			"doctype": "Communication",
			"communication_type": "Communication",
			"content": content,
			"reference_doctype": "Communication",
			"reference_name": a.name
		}).insert()
		c = dataent.get_doc({
			"doctype": "Communication",
			"communication_type": "Communication",
			"content": content,
			"reference_doctype": "Communication",
			"reference_name": b.name
		}).insert()
		a = dataent.get_doc("Communication", a.name)
		a.reference_doctype = "Communication"
		a.reference_name = c.name
		self.assertRaises(dataent.CircularLinkingError, a.save)

