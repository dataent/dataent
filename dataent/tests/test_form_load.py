# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent, unittest
from dataent.desk.form.load import getdoctype, getdoc
from dataent.core.page.permission_manager.permission_manager import update, reset


class TestFormLoad(unittest.TestCase):
	def test_load(self):
		getdoctype("DocType")
		meta = list(filter(lambda d: d.name=="DocType", dataent.response.docs))[0]
		self.assertEqual(meta.name, "DocType")
		self.assertTrue(meta.get("__js"))

		dataent.response.docs = []
		getdoctype("Event")
		meta = list(filter(lambda d: d.name=="Event", dataent.response.docs))[0]
		self.assertTrue(meta.get("__calendar_js"))

	def test_fieldlevel_permissions_in_load(self):
		user = dataent.get_doc('User', 'test@example.com')
		user.remove_roles('Website Manager')
		user.add_roles('Blogger')
		reset('Blog Post')

		dataent.db.sql('update tabDocField set permlevel=1 where fieldname="published" and parent="Blog Post"')

		update('Blog Post', 'Website Manager', 0, 'permlevel', 1)

		dataent.set_user(user.name)

		# print dataent.as_json(get_valid_perms('Blog Post'))

		dataent.clear_cache(doctype='Blog Post')

		blog = dataent.db.get_value('Blog Post', {'title': '_Test Blog Post'})

		getdoc('Blog Post', blog)

		checked = False

		for doc in dataent.response.docs:
			if doc.name == blog:
				self.assertEqual(doc.published, None)
				checked = True

		self.assertTrue(checked, True)

		dataent.db.sql('update tabDocField set permlevel=0 where fieldname="published" and parent="Blog Post"')
		reset('Blog Post')

		dataent.clear_cache(doctype='Blog Post')

		dataent.response.docs = []
		getdoc('Blog Post', blog)

		checked = False

		for doc in dataent.response.docs:
			if doc.name == blog:
				self.assertEqual(doc.published, 1)
				checked = True

		self.assertTrue(checked, True)

		dataent.set_user('Administrator')
