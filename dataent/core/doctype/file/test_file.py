# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest
from dataent.utils.file_manager import save_file, get_files_path
from dataent import _
from dataent.core.doctype.file.file import move_file
# test_records = dataent.get_test_records('File')

class TestFile(unittest.TestCase):
	def setUp(self):
		self.delete_test_data()
		self.upload_file()

	def tearDown(self):
		try:
			dataent.get_doc("File", {"file_name": "file_copy.txt"}).delete()
		except dataent.DoesNotExistError:
			pass

	def delete_test_data(self):
		for f in dataent.db.sql('''select name, file_name from tabFile where
			is_home_folder = 0 and is_attachments_folder = 0 order by rgt-lft asc'''):
			dataent.delete_doc("File", f[0])

	def upload_file(self):
		self.saved_file = save_file('file_copy.txt', "Testing file copy example.",\
			 "", "", self.get_folder("Test Folder 1", "Home").name)
		self.saved_filename = get_files_path(self.saved_file.file_name)

	def get_folder(self, folder_name, parent_folder="Home"):
		return dataent.get_doc({
			"doctype": "File",
			"file_name": _(folder_name),
			"is_folder": 1,
			"folder": _(parent_folder)
		}).insert()

	def tests_after_upload(self):
		self.assertEqual(self.saved_file.folder, _("Home/Test Folder 1"))

		folder_size = dataent.db.get_value("File", _("Home/Test Folder 1"), "file_size")
		saved_file_size = dataent.db.get_value("File", self.saved_file.name, "file_size")

		self.assertEqual(folder_size, saved_file_size)

	def test_file_copy(self):
		folder = self.get_folder("Test Folder 2", "Home")

		file = dataent.get_doc("File", {"file_name":"file_copy.txt"})
		move_file([{"name": file.name}], folder.name, file.folder)
		file = dataent.get_doc("File", {"file_name":"file_copy.txt"})

		self.assertEqual(_("Home/Test Folder 2"), file.folder)
		self.assertEqual(dataent.db.get_value("File", _("Home/Test Folder 2"), "file_size"), file.file_size)
		self.assertEqual(dataent.db.get_value("File", _("Home/Test Folder 1"), "file_size"), 0)

	def test_folder_copy(self):
		folder = self.get_folder("Test Folder 2", "Home")
		folder = self.get_folder("Test Folder 3", "Home/Test Folder 2")

		self.saved_file = save_file('folder_copy.txt', "Testing folder copy example.", "", "", folder.name)

		move_file([{"name": folder.name}], 'Home/Test Folder 1', folder.folder)

		file = dataent.get_doc("File", {"file_name":"folder_copy.txt"})
		file_copy_txt = dataent.get_value("File", {"file_name":"file_copy.txt"})
		if file_copy_txt:
			dataent.get_doc("File", file_copy_txt).delete()

		self.assertEqual(_("Home/Test Folder 1/Test Folder 3"), file.folder)
		self.assertEqual(dataent.db.get_value("File", _("Home/Test Folder 1"), "file_size"), file.file_size)
		self.assertEqual(dataent.db.get_value("File", _("Home/Test Folder 2"), "file_size"), 0)

	def test_non_parent_folder(self):
		d = dataent.get_doc({
			"doctype": "File",
			"file_name": _("Test_Folder"),
			"is_folder": 1
		})

		self.assertRaises(dataent.ValidationError, d.save)

	def test_on_delete(self):
		file = dataent.get_doc("File", {"file_name":"file_copy.txt"})
		file.delete()

		self.assertEqual(dataent.db.get_value("File", _("Home/Test Folder 1"), "file_size"), 0)

		folder = self.get_folder("Test Folder 3", "Home/Test Folder 1")
		self.saved_file = save_file('folder_copy.txt', "Testing folder copy example.", "", "", folder.name)

		folder = dataent.get_doc("File", "Home/Test Folder 1/Test Folder 3")
		self.assertRaises(dataent.ValidationError, folder.delete)

	def test_file_upload_limit(self):
		from dataent.utils.file_manager import MaxFileSizeReachedError
		from dataent.limits import update_limits, clear_limit
		from dataent import _dict

		update_limits({
			'space': 1,
			'space_usage': {
				'files_size': (1024 ** 2),
				'database_size': 0,
				'backup_size': 0,
				'total': (1024 ** 2)
			}
		})

		# Rebuild the dataent.local.conf to take up the changes from site_config
		dataent.local.conf = _dict(dataent.get_site_config())

		self.assertRaises(MaxFileSizeReachedError, save_file, '_test_max_space.txt',
			'This files test for max space usage', "", "", self.get_folder("Test Folder 2", "Home").name)

		# Scrub the site_config and rebuild dataent.local.conf
		clear_limit("space")
		dataent.local.conf = _dict(dataent.get_site_config())
