# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _

from dataent.model.document import Document

class WebsiteSlideshow(Document):
	def validate(self):
		self.validate_images()

	def on_update(self):
		# a slide show can be in use and any change in it should get reflected
		from dataent.website.render import clear_cache
		clear_cache()

	def validate_images(self):
		''' atleast one image file should be public for slideshow '''
		files = map(lambda row: row.image, self.slideshow_items)
		if files:
			result = dataent.get_all("File", filters={ "file_url":("in", files) }, fields="is_private")
			if any([file.is_private for file in result]):
				dataent.throw(_("All Images attached to Website Slideshow should be public"))

def get_slideshow(doc):
	if not doc.slideshow:
		return {}

	slideshow = dataent.get_doc("Website Slideshow", doc.slideshow)

	return {
		"slides": slideshow.get({"doctype":"Website Slideshow Item"}),
		"slideshow_header": slideshow.header or ""
	}
