# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent, unittest, os
from dataent.utils import cint
from dataent.model.naming import revert_series_if_last, make_autoname, parse_naming_series

class TestDocument(unittest.TestCase):
	def test_get_return_empty_list_for_table_field_if_none(self):
		d = dataent.get_doc({"doctype":"User"})
		self.assertEqual(d.get("roles"), [])

	def test_load(self):
		d = dataent.get_doc("DocType", "User")
		self.assertEqual(d.doctype, "DocType")
		self.assertEqual(d.name, "User")
		self.assertEqual(d.allow_rename, 1)
		self.assertTrue(isinstance(d.fields, list))
		self.assertTrue(isinstance(d.permissions, list))
		self.assertTrue(filter(lambda d: d.fieldname=="email", d.fields))

	def test_load_single(self):
		d = dataent.get_doc("Website Settings", "Website Settings")
		self.assertEqual(d.name, "Website Settings")
		self.assertEqual(d.doctype, "Website Settings")
		self.assertTrue(d.disable_signup in (0, 1))

	def test_insert(self):
		d = dataent.get_doc({
			"doctype":"Event",
			"subject":"test-doc-test-event 1",
			"starts_on": "2014-01-01",
			"event_type": "Public"
		})
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEqual(dataent.db.get_value("Event", d.name, "subject"),
			"test-doc-test-event 1")

		# test if default values are added
		self.assertEqual(d.send_reminder, 1)
		return d

	def test_insert_with_child(self):
		d = dataent.get_doc({
			"doctype":"Event",
			"subject":"test-doc-test-event 2",
			"starts_on": "2014-01-01",
			"event_type": "Public"
		})
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEqual(dataent.db.get_value("Event", d.name, "subject"),
			"test-doc-test-event 2")

	def test_update(self):
		d = self.test_insert()
		d.subject = "subject changed"
		d.save()

		self.assertEqual(dataent.db.get_value(d.doctype, d.name, "subject"), "subject changed")

	def test_mandatory(self):
		dataent.delete_doc_if_exists("User", "test_mandatory@example.com")

		d = dataent.get_doc({
			"doctype": "User",
			"email": "test_mandatory@example.com",
		})
		self.assertRaises(dataent.MandatoryError, d.insert)

		d.set("first_name", "Test Mandatory")
		d.insert()
		self.assertEqual(dataent.db.get_value("User", d.name), d.name)

	def test_confict_validation(self):
		d1 = self.test_insert()
		d2 = dataent.get_doc(d1.doctype, d1.name)
		d1.save()
		self.assertRaises(dataent.TimestampMismatchError, d2.save)

	def test_confict_validation_single(self):
		d1 = dataent.get_doc("Website Settings", "Website Settings")
		d1.home_page = "test-web-page-1"

		d2 = dataent.get_doc("Website Settings", "Website Settings")
		d2.home_page = "test-web-page-1"

		d1.save()
		self.assertRaises(dataent.TimestampMismatchError, d2.save)

	def test_permission(self):
		dataent.set_user("Guest")
		self.assertRaises(dataent.PermissionError, self.test_insert)
		dataent.set_user("Administrator")

	def test_permission_single(self):
		dataent.set_user("Guest")
		d = dataent.get_doc("Website Settings", "Website Settigns")
		self.assertRaises(dataent.PermissionError, d.save)
		dataent.set_user("Administrator")

	def test_link_validation(self):
		dataent.delete_doc_if_exists("User", "test_link_validation@example.com")

		d = dataent.get_doc({
			"doctype": "User",
			"email": "test_link_validation@example.com",
			"first_name": "Link Validation",
			"roles": [
				{
					"role": "ABC"
				}
			]
		})
		self.assertRaises(dataent.LinkValidationError, d.insert)

		d.roles = []
		d.append("roles", {
			"role": "System Manager"
		})
		d.insert()

		self.assertEqual(dataent.db.get_value("User", d.name), d.name)

	def test_validate(self):
		d = self.test_insert()
		d.starts_on = "2014-01-01"
		d.ends_on = "2013-01-01"
		self.assertRaises(dataent.ValidationError, d.validate)
		self.assertRaises(dataent.ValidationError, d.run_method, "validate")
		self.assertRaises(dataent.ValidationError, d.save)

	def test_update_after_submit(self):
		d = self.test_insert()
		d.starts_on = "2014-09-09"
		self.assertRaises(dataent.UpdateAfterSubmitError, d.validate_update_after_submit)
		d.meta.get_field("starts_on").allow_on_submit = 1
		d.validate_update_after_submit()
		d.meta.get_field("starts_on").allow_on_submit = 0

		# when comparing date(2014, 1, 1) and "2014-01-01"
		d.reload()
		d.starts_on = "2014-01-01"
		d.validate_update_after_submit()

	def test_varchar_length(self):
		d = self.test_insert()
		d.subject = "abcde"*100
		self.assertRaises(dataent.CharacterLengthExceededError, d.save)

	def test_xss_filter(self):
		d = self.test_insert()

		# script
		xss = '<script>alert("XSS")</script>'
		escaped_xss = xss.replace('<', '&lt;').replace('>', '&gt;')
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

		# onload
		xss = '<div onload="alert("XSS")">Test</div>'
		escaped_xss = '<div>Test</div>'
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

		# css attributes
		xss = '<div style="something: doesn\'t work; color: red;">Test</div>'
		escaped_xss = '<div style="color: red;">Test</div>'
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

	def test_link_count(self):
		if os.environ.get('CI'):
			# cannot run this test reliably in travis due to its handling
			# of parallelism
			return

		from dataent.model.utils.link_count import update_link_count

		update_link_count()

		doctype, name = 'User', 'test@example.com'

		d = self.test_insert()
		d.append('event_participants', {"reference_doctype": doctype, "reference_docname": name})

		d.save()

		link_count = dataent.cache().get_value('_link_count') or {}
		old_count = link_count.get((doctype, name)) or 0

		dataent.db.commit()

		link_count = dataent.cache().get_value('_link_count') or {}
		new_count = link_count.get((doctype, name)) or 0

		self.assertEqual(old_count + 1, new_count)

		before_update = dataent.db.get_value(doctype, name, 'idx')

		update_link_count()

		after_update = dataent.db.get_value(doctype, name, 'idx')

		self.assertEqual(before_update + new_count, after_update)

	def test_naming_series(self):
		data = ["TEST-", "TEST/17-18/.test_data./.####", "TEST.YYYY.MM.####"]

		for series in data:
			name = make_autoname(series)
			prefix = series

			if ".#" in series:
				prefix = series.rsplit('.',1)[0]

			prefix = parse_naming_series(prefix)
			old_current = dataent.db.get_value('Series', prefix, "current", order_by="name")

			revert_series_if_last(series, name)
			new_current = cint(dataent.db.get_value('Series', prefix, "current", order_by="name"))

			self.assertEqual(cint(old_current) - 1, new_current)
