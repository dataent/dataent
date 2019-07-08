# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document

class PrintStyle(Document):
	def validate(self):
		if (self.standard==1
			and not dataent.local.conf.get("developer_mode")
			and not (dataent.flags.in_import or dataent.flags.in_test)):

			dataent.throw(dataent._("Standard Print Style cannot be changed. Please duplicate to edit."))

	def on_update(self):
		self.export_doc()

	def export_doc(self):
		# export
		from dataent.modules.utils import export_module_json
		export_module_json(self, self.standard == 1, 'Printing')
