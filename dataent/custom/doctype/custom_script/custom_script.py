# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import dataent

from dataent.model.document import Document

class CustomScript(Document):
	def autoname(self):
		if not self.script_type:
			self.script_type = 'Client'
		self.name = self.dt + "-" + self.script_type

	def on_update(self):
		dataent.clear_cache(doctype=self.dt)

	def on_trash(self):
		dataent.clear_cache(doctype=self.dt)

