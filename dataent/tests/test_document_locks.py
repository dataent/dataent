# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent, unittest

class TestDocumentLocks(unittest.TestCase):
	def test_locking(self):
		todo = dataent.get_doc(dict(doctype='ToDo', description='test')).insert()
		todo_1 = dataent.get_doc('ToDo', todo.name)

		todo.lock()
		self.assertRaises(dataent.DocumentLockedError, todo_1.lock)
		todo.unlock()

		todo_1.lock()
		self.assertRaises(dataent.DocumentLockedError, todo.lock)
		todo_1.unlock()
