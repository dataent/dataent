# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import unittest, dataent, os
from dataent.utils import get_url
from dataent.core.doctype.user.user import generate_keys

import requests
import base64


class TestAPI(unittest.TestCase):
	def test_insert_many(self):
		if os.environ.get('CI'):
			return
		from dataent.dataentclient import DataentClient

		dataent.db.sql('delete from `tabToDo` where description like "Test API%"')
		dataent.db.commit()

		server = DataentClient(get_url(), "Administrator", "admin", verify=False)

		server.insert_many([
			{"doctype": "ToDo", "description": "Test API 1"},
			{"doctype": "ToDo", "description": "Test API 2"},
			{"doctype": "ToDo", "description": "Test API 3"},
		])

		self.assertTrue(dataent.db.get_value('ToDo', {'description': 'Test API 1'}))
		self.assertTrue(dataent.db.get_value('ToDo', {'description': 'Test API 2'}))
		self.assertTrue(dataent.db.get_value('ToDo', {'description': 'Test API 3'}))

	def test_auth_via_api_key_secret(self):

		# generate api ke and api secret for administrator
		keys = generate_keys("Administrator")
		dataent.db.commit()
		generated_secret = dataent.utils.password.get_decrypted_password(
			"User", "Administrator", fieldname='api_secret'
		)

		api_key = dataent.db.get_value("User", "Administrator", "api_key")
		header = {"Authorization": "token {}:{}".format(api_key, generated_secret)}
		res = requests.post(dataent.get_site_config().host_name + "/api/method/dataent.auth.get_logged_user", headers=header)

		self.assertEqual(res.status_code, 200)
		self.assertEqual("Administrator", res.json()["message"])
		self.assertEqual(keys['api_secret'], generated_secret)

		header = {"Authorization": "Basic {}".format(base64.b64encode(dataent.safe_encode("{}:{}".format(api_key, generated_secret))).decode())}
		res = requests.post(dataent.get_site_config().host_name + "/api/method/dataent.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 200)
		self.assertEqual("Administrator", res.json()["message"])

		# Valid api key, invalid api secret
		api_secret = "ksk&93nxoe3os"
		header = {"Authorization": "token {}:{}".format(api_key, api_secret)}
		res = requests.post(dataent.get_site_config().host_name + "/api/method/dataent.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 403)


		# random api key and api secret
		api_key = "@3djdk3kld"
		api_secret = "ksk&93nxoe3os"
		header = {"Authorization": "token {}:{}".format(api_key, api_secret)}
		res = requests.post(dataent.get_site_config().host_name + "/api/method/dataent.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 401)