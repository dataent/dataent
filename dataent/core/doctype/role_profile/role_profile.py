# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from dataent.model.document import Document

class RoleProfile(Document):
	def autoname(self):
		"""set name as Role Profile name"""
		self.name = self.role_profile

	def on_update(self):
		""" Changes in role_profile reflected across all its user """
		from dataent.core.doctype.user.user import update_roles
		update_roles(self.name)
