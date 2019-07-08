# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: See license.txt

from __future__ import unicode_literals
import dataent
from dataent import throw, _

from dataent.model.document import Document

class Currency(Document):
	def validate(self):
		if not dataent.flags.in_install_app:
			dataent.clear_cache()
