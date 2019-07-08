# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest

# test_records = dataent.get_test_records('ToDo')

class TestToDo(unittest.TestCase):
	def test_delete(self):
		todo = dataent.get_doc(dict(doctype='ToDo', description='test todo',
			assigned_by='Administrator')).insert()

		dataent.db.sql('delete from `tabDeleted Document`')
		todo.delete()

		deleted = dataent.get_doc('Deleted Document', dict(deleted_doctype=todo.doctype, deleted_name=todo.name))
		self.assertEqual(todo.as_json(), deleted.data)

	def test_fetch(self):
		todo = dataent.get_doc(dict(doctype='ToDo', description='test todo',
			assigned_by='Administrator')).insert()
		self.assertEqual(todo.assigned_by_full_name,
			dataent.db.get_value('User', todo.assigned_by, 'full_name'))

	def test_fetch_setup(self):
		dataent.db.sql('delete from tabToDo')

		todo_meta = dataent.get_doc('DocType', 'ToDo')
		todo_meta.get('fields', dict(fieldname='assigned_by_full_name'))[0].fetch_from = ''
		todo_meta.save()

		dataent.clear_cache(doctype='ToDo')

		todo = dataent.get_doc(dict(doctype='ToDo', description='test todo',
			assigned_by='Administrator')).insert()
		self.assertFalse(todo.assigned_by_full_name)

		todo_meta = dataent.get_doc('DocType', 'ToDo')
		todo_meta.get('fields', dict(fieldname='assigned_by_full_name'))[0].fetch_from = 'assigned_by.full_name'
		todo_meta.save()

		todo.reload()

		self.assertEqual(todo.assigned_by_full_name,
			dataent.db.get_value('User', todo.assigned_by, 'full_name'))

def test_fetch_if_empty(self):
		dataent.db.sql('delete from tabToDo')

		# Allow user changes
		todo_meta = dataent.get_doc('DocType', 'ToDo')
		field = todo_meta.get('fields', dict(fieldname='assigned_by_full_name'))[0]
		field.fetch_from = 'assigned_by.full_name'
		field.fetch_if_empty = 1
		todo_meta.save()

		dataent.clear_cache(doctype='ToDo')

		todo = dataent.get_doc(dict(doctype='ToDo', description='test todo',
			assigned_by='Administrator', assigned_by_full_name='Admin')).insert()

		self.assertEqual(todo.assigned_by_full_name, 'Admin')

		# Overwrite user changes
		todo_meta = dataent.get_doc('DocType', 'ToDo')
		todo_meta.get('fields', dict(fieldname='assigned_by_full_name'))[0].fetch_if_empty = 0
		todo_meta.save()

		todo.reload()
		todo.save()

		self.assertEqual(todo.assigned_by_full_name,
			dataent.db.get_value('User', todo.assigned_by, 'full_name'))
