# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document

class ErrorSnapshot(Document):
	no_feed_on_delete = True

	def onload(self):
		if not self.parent_error_snapshot:
			self.db_set('seen', True, update_modified=False)

			for relapsed in dataent.get_all("Error Snapshot", filters={"parent_error_snapshot": self.name}):
				dataent.db.set_value("Error Snapshot", relapsed.name, "seen", True, update_modified=False)

			dataent.local.flags.commit = True

	def validate(self):
		parent = dataent.get_all("Error Snapshot",
			filters={"evalue": self.evalue, "parent_error_snapshot": ""},
			fields=["name", "relapses", "seen"], limit_page_length=1)

		if parent:
			parent = parent[0]
			self.update({"parent_error_snapshot": parent['name']})
			dataent.db.set_value('Error Snapshot', parent['name'], 'relapses', parent["relapses"] + 1)
			if parent["seen"]:
				dataent.db.set_value("Error Snapshot", parent["name"], "seen", False)
