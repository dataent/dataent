# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document

class EmailGroupMember(Document):
	def after_delete(self):
		email_group = dataent.get_doc('Email Group', self.email_group)
		email_group.update_total_subscribers()

	def after_insert(self):
		email_group = dataent.get_doc('Email Group', self.email_group)
		email_group.update_total_subscribers()

def after_doctype_insert():
	dataent.db.add_unique("Email Group Member", ("email_group", "email"))
