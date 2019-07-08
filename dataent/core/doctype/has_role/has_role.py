# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document

class HasRole(Document):
	def before_insert(self):
		if dataent.db.exists("Has Role", {"parent": self.parent, "role": self.role}):
			dataent.throw(dataent._("User '{0}' already has the role '{1}'").format(self.parent, self.role))
