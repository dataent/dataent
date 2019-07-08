# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

from __future__ import unicode_literals
import dataent
import unittest

test_records = dataent.get_test_records('Note')

class TestNote(unittest.TestCase):
	def insert_note(self):
		dataent.db.sql('delete from tabVersion')
		dataent.db.sql('delete from tabNote')
		dataent.db.sql('delete from `tabNote Seen By`')

		return dataent.get_doc(dict(doctype='Note', title='test note',
			content='test note content')).insert()

	def test_version(self):
		note = self.insert_note()
		note.title = 'test note 1'
		note.content = '1'
		note.save()

		version = dataent.get_doc('Version', dict(docname=note.name))
		data = version.get_data()

		self.assertTrue(('title', 'test note', 'test note 1'), data['changed'])
		self.assertTrue(('content', 'test note content', '1'), data['changed'])

	def test_rows(self):
		note = self.insert_note()

		# test add
		note.append('seen_by', {'user': 'Administrator'})
		note.save()

		version = dataent.get_doc('Version', dict(docname=note.name))
		data = version.get_data()

		self.assertEqual(len(data.get('added')), 1)
		self.assertEqual(len(data.get('removed')), 0)
		self.assertEqual(len(data.get('changed')), 0)

		for row in data.get('added'):
			self.assertEqual(row[0], 'seen_by')
			self.assertEqual(row[1]['user'], 'Administrator')

		# test row change
		note.seen_by[0].user = 'Guest'
		note.save()

		version = dataent.get_doc('Version', dict(docname=note.name))
		data = version.get_data()

		self.assertEqual(len(data.get('row_changed')), 1)
		for row in data.get('row_changed'):
			self.assertEqual(row[0], 'seen_by')
			self.assertEqual(row[1], 0)
			self.assertEqual(row[2], note.seen_by[0].name)
			self.assertEqual(row[3], [['user', 'Administrator', 'Guest']])

		# test remove
		note.seen_by = []
		note.save()

		version = dataent.get_doc('Version', dict(docname=note.name))
		data = version.get_data()

		self.assertEqual(len(data.get('removed')), 1)
		for row in data.get('removed'):
			self.assertEqual(row[0], 'seen_by')
			self.assertEqual(row[1]['user'], 'Guest')

		# self.assertTrue(('title', 'test note', 'test note 1'), data['changed'])
		# self.assertTrue(('content', 'test note content', '1'), data['changed'])
