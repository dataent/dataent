#  -*- coding: utf-8 -*-

# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals

import dataent
import unittest

test_records = dataent.get_test_records('Custom Field')

from dataent.model.db_schema import InvalidColumnName

class TestCustomField(unittest.TestCase):
	pass
