# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals
import dataent, json, os
import unittest

test_records = dataent.get_test_records('Report')

class TestReport(unittest.TestCase):
	def test_report_builder(self):
		if dataent.db.exists('Report', 'User Activity Report'):
			dataent.delete_doc('Report', 'User Activity Report')

		with open(os.path.join(os.path.dirname(__file__), 'user_activity_report.json'), 'r') as f:
			dataent.get_doc(json.loads(f.read())).insert()

		report = dataent.get_doc('Report', 'User Activity Report')
		columns, data = report.get_data()
		self.assertEqual(columns[0].get('label'), 'ID')
		self.assertEqual(columns[1].get('label'), 'User Type')
		self.assertTrue('Administrator' in [d[0] for d in data])

	def test_query_report(self):
		report = dataent.get_doc('Report', 'Permitted Documents For User')
		columns, data = report.get_data(filters={'user': 'Administrator', 'doctype': 'DocType'})
		self.assertEqual(columns[0].get('label'), 'Name')
		self.assertEqual(columns[1].get('label'), 'Module')
		self.assertTrue('User' in [d[0] for d in data])

	def test_report_permisisons(self):
		dataent.db.sql("""delete from `tabHas Role` where parent = %s
			and role = 'Test Has Role'""", dataent.session.user, auto_commit=1)

		if not dataent.db.exists('Role', 'Test Has Role'):
			role = dataent.get_doc({
				'doctype': 'Role',
				'role_name': 'Test Has Role'
			}).insert(ignore_permissions=True)

		if not dataent.db.exists("Report", "Test Report"):
			report = dataent.get_doc({
				'doctype': 'Report',
				'ref_doctype': 'User',
				'report_name': 'Test Report',
				'report_type': 'Query Report',
				'is_standard': 'No',
				'roles': [
					{'role': 'Test Has Role'}
				]
			}).insert(ignore_permissions=True)
		else:
			report = dataent.get_doc('Report', 'Test Report')

		self.assertNotEquals(report.is_permitted(), True)

	# test for the `_format` method if report data doesn't have sort_by parameter
	def test_format_method(self):
		if dataent.db.exists('Report', 'User Activity Report Without Sort'):
			dataent.delete_doc('Report', 'User Activity Report Without Sort')
		with open(os.path.join(os.path.dirname(__file__), 'user_activity_report_without_sort.json'), 'r') as f:
			dataent.get_doc(json.loads(f.read())).insert()

		report = dataent.get_doc('Report', 'User Activity Report Without Sort')
		columns, data = report.get_data()

		self.assertEqual(columns[0].get('label'), 'ID')
		self.assertEqual(columns[1].get('label'), 'User Type')
		self.assertTrue('Administrator' in [d[0] for d in data])
		dataent.delete_doc('Report', 'User Activity Report Without Sort')
