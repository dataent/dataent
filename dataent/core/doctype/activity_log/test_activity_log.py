# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest
import time
from dataent.auth import LoginManager, CookieManager

class TestActivityLog(unittest.TestCase):
	def test_activity_log(self):

		# test user login log
		dataent.local.form_dict = dataent._dict({
			'cmd': 'login',
			'sid': 'Guest',
			'pwd': 'admin',
			'usr': 'Administrator'
		})

		dataent.local.cookie_manager = CookieManager()
		dataent.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, 'Success')

		# test user logout log
		dataent.local.login_manager.logout()
		auth_log = self.get_auth_log(operation='Logout')
		self.assertEqual(auth_log.status, 'Success')

		# test invalid login
		dataent.form_dict.update({ 'pwd': 'password' })
		self.assertRaises(dataent.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, 'Failed')

		dataent.local.form_dict = dataent._dict()

	def get_auth_log(self, operation='Login'):
		names = dataent.db.sql_list("""select name from `tabActivity Log`
					where user='Administrator' and operation='{operation}' order by
					creation desc""".format(operation=operation))

		name = names[0]
		auth_log = dataent.get_doc('Activity Log', name)
		return auth_log

	def test_brute_security(self):
		update_system_settings({
			'allow_consecutive_login_attempts': 3,
			'allow_login_after_fail': 5
		})

		dataent.local.form_dict = dataent._dict({
			'cmd': 'login',
			'sid': 'Guest',
			'pwd': 'admin',
			'usr': 'Administrator'
		})

		dataent.local.cookie_manager = CookieManager()
		dataent.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEquals(auth_log.status, 'Success')

		# test user logout log
		dataent.local.login_manager.logout()
		auth_log = self.get_auth_log(operation='Logout')
		self.assertEquals(auth_log.status, 'Success')

		# test invalid login
		dataent.form_dict.update({ 'pwd': 'password' })
		self.assertRaises(dataent.AuthenticationError, LoginManager)
		self.assertRaises(dataent.AuthenticationError, LoginManager)
		self.assertRaises(dataent.AuthenticationError, LoginManager)
		self.assertRaises(dataent.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(dataent.AuthenticationError, LoginManager)

		dataent.local.form_dict = dataent._dict()

def update_system_settings(args):
	doc = dataent.get_doc('System Settings')
	doc.update(args)
	doc.save()
