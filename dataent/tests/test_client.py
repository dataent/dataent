# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors

from __future__ import unicode_literals

import unittest, dataent

class TestClient(unittest.TestCase):
	def test_set_value(self):
		todo = dataent.get_doc(dict(doctype='ToDo', description='test')).insert()
		dataent.set_value('ToDo', todo.name, 'description', 'test 1')
		self.assertEqual(dataent.get_value('ToDo', todo.name, 'description'), 'test 1')

		dataent.set_value('ToDo', todo.name, {'description': 'test 2'})
		self.assertEqual(dataent.get_value('ToDo', todo.name, 'description'), 'test 2')

	def test_delete(self):
		from dataent.client import delete

		todo = dataent.get_doc(dict(doctype='ToDo', description='description')).insert()
		delete("ToDo", todo.name)

		self.assertFalse(dataent.db.exists("ToDo", todo.name))
		self.assertRaises(dataent.DoesNotExistError, delete, "ToDo", todo.name)
