# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent, os
from dataent.model.document import Document

class TestRunner(Document):
	pass

@dataent.whitelist()
def get_test_js(test_path=None):
	'''Get test + data for app, example: app/tests/ui/test_name.js'''
	if not test_path:
		test_path = dataent.db.get_single_value('Test Runner', 'module_path')
	test_js = []

	# split
	app, test_path = test_path.split(os.path.sep, 1)

	# now full path
	test_path = dataent.get_app_path(app, test_path)

	def add_file(path):
		with open(path, 'r') as fileobj:
			test_js.append(dict(
				script = fileobj.read()
			))

	# add test_lib.js
	add_file(dataent.get_app_path('dataent', 'tests', 'ui', 'data', 'test_lib.js'))
	add_file(test_path)

	return test_js

