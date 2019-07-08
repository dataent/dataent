# -*- coding: utf-8 -*-
# Copyright (c) 2018, Dataent Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest
import hashlib

test_records = []
class TestTransactionLog(unittest.TestCase):

	def test_validate_chaining(self):
		dataent.get_doc({
			"doctype": "Transaction Log",
			"reference_doctype": "Test Doctype",
			"document_name": "Test Document 1",
			"data": "first_data"
		}).insert(ignore_permissions=True)

		second_log = dataent.get_doc({
						"doctype": "Transaction Log",
						"reference_doctype": "Test Doctype",
						"document_name": "Test Document 2",
						"data": "second_data"
					}).insert(ignore_permissions=True)

		third_log = dataent.get_doc({
						"doctype": "Transaction Log",
						"reference_doctype": "Test Doctype",
						"document_name": "Test Document 3",
						"data": "third_data"
					}).insert(ignore_permissions=True)


		sha = hashlib.sha256()
		sha.update(
			dataent.safe_encode(str(third_log.transaction_hash)) + 
			dataent.safe_encode(str(second_log.chaining_hash))
		)

		self.assertEqual(sha.hexdigest(), third_log.chaining_hash)
