# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent
import unittest

test_records = dataent.get_test_records('Role')

class TestUser(unittest.TestCase):
	def test_disable_role(self):
		dataent.get_doc("User", "test@example.com").add_roles("_Test Role 3")
		
		role = dataent.get_doc("Role", "_Test Role 3")
		role.disabled = 1
		role.save()
		
		self.assertTrue("_Test Role 3" not in dataent.get_roles("test@example.com"))
		
		dataent.get_doc("User", "test@example.com").add_roles("_Test Role 3")
		self.assertTrue("_Test Role 3" not in dataent.get_roles("test@example.com"))
		
		role = dataent.get_doc("Role", "_Test Role 3")
		role.disabled = 0
		role.save()
		
		dataent.get_doc("User", "test@example.com").add_roles("_Test Role 3")
		self.assertTrue("_Test Role 3" in dataent.get_roles("test@example.com"))
		