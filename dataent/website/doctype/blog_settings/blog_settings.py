# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import dataent

from dataent.model.document import Document

class BlogSettings(Document):
		
	def on_update(self):
		from dataent.website.render import clear_cache
		clear_cache("blog")
		clear_cache("writers")