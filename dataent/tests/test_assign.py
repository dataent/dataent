# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent, unittest
import dataent.desk.form.assign_to

class TestAssign(unittest.TestCase):
	def test_assign(self):
		todo = dataent.get_doc({"doctype":"ToDo", "description": "test"}).insert()
		if not dataent.db.exists("User", "test@example.com"):
			dataent.get_doc({"doctype":"User", "email":"test@example.com", "first_name":"Test"}).insert()

		added = dataent.desk.form.assign_to.add({
			"assign_to": "test@example.com",
			"doctype": todo.doctype,
			"name": todo.name,
			"description": todo.description,
		})

		self.assertTrue("test@example.com" in [d.owner for d in added])

		removed = dataent.desk.form.assign_to.remove(todo.doctype, todo.name, "test@example.com")
		self.assertTrue("test@example.com" not in [d.owner for d in removed])
