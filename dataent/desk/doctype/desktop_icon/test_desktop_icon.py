# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest

from dataent.desk.doctype.desktop_icon.desktop_icon import (get_desktop_icons, add_user_icon,
	set_hidden_list, set_order, clear_desktop_icons_cache)

# test_records = dataent.get_test_records('Desktop Icon')

class TestDesktopIcon(unittest.TestCase):
	def setUp(self):
		dataent.set_user('test@example.com')
		dataent.db.sql('delete from `tabDesktop Icon` where standard=0')
		dataent.db.sql('delete from `tabBlock Module`')
		dataent.db.sql('update `tabDesktop Icon` set hidden=0, blocked=0')

	def tearDown(self):
		dataent.set_user('Administrator')

	def get_icon(self, module_name):
		for i in get_desktop_icons():
			if i.module_name == module_name:
				return i

		return None

	def test_get_standard_desktop_icon_for_user(self):
		self.assertEqual(self.get_icon('Desk').standard, 1)

	def test_add_desktop_icon(self):
		self.assertEqual(self.get_icon('User'), None)
		add_user_icon('User')

		icon = self.get_icon('User')
		self.assertEqual(icon.custom, 1)
		self.assertEqual(icon.standard, 0)

	def test_hide_desktop_icon(self):
		set_hidden_list(["Desk"], 'test@example.com')

		icon = self.get_icon('Desk')
		self.assertEqual(icon.hidden, 1)
		self.assertEqual(icon.standard, 0)

	def test_remove_custom_desktop_icon_on_hidden(self):
		self.test_add_desktop_icon()
		set_hidden_list(['User'], 'test@example.com')

		icon = self.get_icon('User')
		self.assertEqual(icon, None)

	def test_show_desktop_icon(self):
		self.test_hide_desktop_icon()
		set_hidden_list([], 'test@example.com')

		icon = self.get_icon('Desk')
		self.assertEqual(icon.hidden, 0)
		self.assertEqual(icon.standard, 0)

	def test_globally_hidden_desktop_icon(self):
		set_hidden_list(["Desk"])

		icon = self.get_icon('Desk')
		self.assertEqual(icon.hidden, 1)

		dataent.set_user('test1@example.com')
		icon = self.get_icon('Desk')
		self.assertEqual(icon.hidden, 1)

	def test_re_order_desktop_icons(self):
		icons = [d.module_name for d in get_desktop_icons()]
		m0, m1 = icons[0], icons[1]
		set_order([m1, m0] + icons[2:], dataent.session.user)

		# reload
		icons = [d.module_name for d in get_desktop_icons()]

		# check switched order
		self.assertEqual(icons[0], m1)
		self.assertEqual(icons[1], m0)

	def test_block_desktop_icons_for_user(self):
		def test_unblock():
			user = dataent.get_doc('User', 'test@example.com')
			user.block_modules = []
			user.save(ignore_permissions = 1)

			icon = self.get_icon('Desk')
			self.assertEqual(icon.hidden, 0)

		test_unblock()

		user = dataent.get_doc('User', 'test@example.com')
		user.append('block_modules', {'module': 'Desk'})
		user.save(ignore_permissions = 1)
		clear_desktop_icons_cache(user.name)

		icon = self.get_icon('Desk')
		self.assertEqual(icon.hidden, 1)

		test_unblock()


