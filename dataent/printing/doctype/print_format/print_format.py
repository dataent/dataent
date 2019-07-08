# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
import dataent.utils
import json
from dataent.utils.jinja import validate_template

from dataent.model.document import Document

class PrintFormat(Document):
	def validate(self):
		if (self.standard=="Yes"
			and not dataent.local.conf.get("developer_mode")
			and not (dataent.flags.in_import or dataent.flags.in_test)):

			dataent.throw(dataent._("Standard Print Format cannot be updated"))

		# old_doc_type is required for clearing item cache
		self.old_doc_type = dataent.db.get_value('Print Format',
				self.name, 'doc_type')

		self.extract_images()

		if not self.module:
			self.module = dataent.db.get_value('DocType', self.doc_type, 'module')

		if self.html and self.print_format_type != 'Js':
			validate_template(self.html)

	def extract_images(self):
		from dataent.utils.file_manager import extract_images_from_html
		if self.format_data:
			data = json.loads(self.format_data)
			for df in data:
				if df.get('fieldtype') and df['fieldtype'] in ('HTML', 'Custom HTML') and df.get('options'):
					df['options'] = extract_images_from_html(self, df['options'])
			self.format_data = json.dumps(data)

	def on_update(self):
		if hasattr(self, 'old_doc_type') and self.old_doc_type:
			dataent.clear_cache(doctype=self.old_doc_type)
		if self.doc_type:
			dataent.clear_cache(doctype=self.doc_type)

		self.export_doc()

	def export_doc(self):
		# export
		from dataent.modules.utils import export_module_json
		export_module_json(self, self.standard == 'Yes', self.module)

	def on_trash(self):
		if self.doc_type:
			dataent.clear_cache(doctype=self.doc_type)

@dataent.whitelist()
def make_default(name):
	"""Set print format as default"""
	dataent.has_permission("Print Format", "write")

	print_format = dataent.get_doc("Print Format", name)

	if (dataent.conf.get('developer_mode') or 0) == 1:
		# developer mode, set it default in doctype
		doctype = dataent.get_doc("DocType", print_format.doc_type)
		doctype.default_print_format = name
		doctype.save()
	else:
		# customization
		dataent.make_property_setter({
			'doctype_or_field': "DocType",
			'doctype': print_format.doc_type,
			'property': "default_print_format",
			'value': name,
		})

	dataent.msgprint(dataent._("{0} is now default print format for {1} doctype").format(
		dataent.bold(name),
		dataent.bold(print_format.doc_type)
	))
