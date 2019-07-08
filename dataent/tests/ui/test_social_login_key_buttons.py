# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import unittest, dataent, time
from dataent.utils.selenium_testdriver import TestDriver

class TestSocialLoginKeyButtons(unittest.TestCase):
	def setUp(self):
		try:
			dataent_login_key = dataent.get_doc("Social Login Key", "dataent")
		except dataent.DoesNotExistError:
			dataent_login_key = dataent.new_doc("Social Login Key")
		dataent_login_key.get_social_login_provider("Dataent", initialize=True)
		dataent_login_key.base_url = "http://localhost:8000"
		dataent_login_key.enable_social_login = 1
		dataent_login_key.client_id = "test_client_id"
		dataent_login_key.client_secret = "test_client_secret"
		dataent_login_key.save()

		self.driver = TestDriver()

	def test_login_buttons(self):

		# Go to Login Page
		self.driver.get("login")

		time.sleep(2)
		dataent_social_login = self.driver.find(".btn-dataent")
		self.assertTrue(len(dataent_social_login) > 0)

	def tearDown(self):
		self.driver.close()
