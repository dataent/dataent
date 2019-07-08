# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent import _

class EmailUnsubscribe(Document):
	def validate(self):
		if not self.global_unsubscribe and not (self.reference_doctype and self.reference_name):
			dataent.throw(_("Reference DocType and Reference Name are required"), dataent.MandatoryError)

		if not self.global_unsubscribe and dataent.db.get_value(self.doctype, self.name, "global_unsubscribe"):
			dataent.throw(_("Delete this record to allow sending to this email address"))

		if self.global_unsubscribe:
			if dataent.get_all("Email Unsubscribe",
				filters={"email": self.email, "global_unsubscribe": 1, "name": ["!=", self.name]}):
				dataent.throw(_("{0} already unsubscribed").format(self.email), dataent.DuplicateEntryError)

		else:
			if dataent.get_all("Email Unsubscribe",
				filters={
					"email": self.email,
					"reference_doctype": self.reference_doctype,
					"reference_name": self.reference_name,
					"name": ["!=", self.name]
				}):
				dataent.throw(_("{0} already unsubscribed for {1} {2}").format(
					self.email, self.reference_doctype, self.reference_name),
					dataent.DuplicateEntryError)

	def on_update(self):
		if self.reference_doctype and self.reference_name:
			doc = dataent.get_doc(self.reference_doctype, self.reference_name)
			doc.add_comment("Label", _("Left this conversation"), comment_by=self.email)

