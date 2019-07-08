#  -*- coding: utf-8 -*-

# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import unittest
import dataent
from dataent.custom.doctype.custom_field.custom_field import create_custom_field

class TestDB(unittest.TestCase):
	def test_get_value(self):
		self.assertEqual(dataent.db.get_value("User", {"name": ["=", "Administrator"]}), "Administrator")
		self.assertEqual(dataent.db.get_value("User", {"name": ["like", "Admin%"]}), "Administrator")
		self.assertNotEquals(dataent.db.get_value("User", {"name": ["!=", "Guest"]}), "Guest")
		self.assertEqual(dataent.db.get_value("User", {"name": ["<", "B"]}), "Administrator")
		self.assertEqual(dataent.db.get_value("User", {"name": ["<=", "Administrator"]}), "Administrator")

		self.assertEqual(dataent.db.sql("""select name from `tabUser` where name > "s" order by modified desc""")[0][0],
			dataent.db.get_value("User", {"name": [">", "s"]}))

		self.assertEqual(dataent.db.sql("""select name from `tabUser` where name >= "t" order by modified desc""")[0][0],
			dataent.db.get_value("User", {"name": [">=", "t"]}))

	def test_escape(self):
		dataent.db.escape("香港濟生堂製藥有限公司 - IT".encode("utf-8"))

	# def test_multiple_queries(self):
	# 	# implicit commit
	# 	self.assertRaises(dataent.SQLError, dataent.db.sql, """select name from `tabUser`; truncate `tabEmail Queue`""")

	def test_log_touched_tables(self):
		dataent.flags.in_migrate = True
		dataent.flags.touched_tables = set()
		dataent.db.set_value('System Settings', 'System Settings', 'backup_limit', 5)
		self.assertIn('tabSingles', dataent.flags.touched_tables)

		dataent.flags.touched_tables = set()
		todo = dataent.get_doc({'doctype': 'ToDo', 'description': 'Random Description'})
		todo.save()
		self.assertIn('tabToDo', dataent.flags.touched_tables)

		dataent.flags.touched_tables = set()
		todo.description = "Another Description"
		todo.save()
		self.assertIn('tabToDo', dataent.flags.touched_tables)

		dataent.flags.touched_tables = set()
		dataent.db.sql("UPDATE tabToDo SET description = 'Updated Description'")
		self.assertNotIn('tabToDo SET', dataent.flags.touched_tables)
		self.assertIn('tabToDo', dataent.flags.touched_tables)

		dataent.flags.touched_tables = set()
		todo.delete()
		self.assertIn('tabToDo', dataent.flags.touched_tables)

		dataent.flags.touched_tables = set()
		create_custom_field('ToDo', {'label': 'ToDo Custom Field'})

		self.assertIn('tabToDo', dataent.flags.touched_tables)
		self.assertIn('tabCustom Field', dataent.flags.touched_tables)
		dataent.flags.in_migrate = False
		dataent.flags.touched_tables.clear()
