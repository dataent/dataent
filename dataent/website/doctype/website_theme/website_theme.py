# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.model.document import Document

class WebsiteTheme(Document):
	def validate(self):
		self.validate_if_customizable()
		self.validate_colors()

	def on_update(self):
		if (not self.custom
			and dataent.local.conf.get('developer_mode')
			and not (dataent.flags.in_import or dataent.flags.in_test)):

			self.export_doc()

		self.clear_cache_if_current_theme()

	def is_standard_and_not_valid_user(self):
		return (not self.custom
			and not dataent.local.conf.get('developer_mode')
			and not (dataent.flags.in_import or dataent.flags.in_test))

	def on_trash(self):
		if self.is_standard_and_not_valid_user():
			dataent.throw(_("You are not allowed to delete a standard Website Theme"),
				dataent.PermissionError)

	def validate_if_customizable(self):
		if self.is_standard_and_not_valid_user():
			dataent.throw(_("Please Duplicate this Website Theme to customize."))

	def validate_colors(self):
		if (self.top_bar_color or self.top_bar_text_color) and \
			self.top_bar_color==self.top_bar_text_color:
				dataent.throw(_("Top Bar Color and Text Color are the same. They should be have good contrast to be readable."))


	def export_doc(self):
		"""Export to standard folder `[module]/website_theme/[name]/[name].json`."""
		from dataent.modules.export_file import export_to_files
		export_to_files(record_list=[['Website Theme', self.name]], create_init=True)


	def clear_cache_if_current_theme(self):
		website_settings = dataent.get_doc("Website Settings", "Website Settings")
		if getattr(website_settings, "website_theme", None) == self.name:
			website_settings.clear_cache()

	def use_theme(self):
		use_theme(self.name)

@dataent.whitelist()
def use_theme(theme):
	website_settings = dataent.get_doc("Website Settings", "Website Settings")
	website_settings.website_theme = theme
	website_settings.ignore_validate = True
	website_settings.save()

def add_website_theme(context):
	bootstrap = dataent.get_hooks("bootstrap")[0]
	bootstrap = [bootstrap]
	context.theme = dataent._dict()

	if not context.disable_website_theme:
		website_theme = get_active_theme()
		context.theme = website_theme and website_theme.as_dict() or dataent._dict()

		if website_theme:
			if website_theme.bootstrap:
				bootstrap.append(website_theme.bootstrap)

			context.web_include_css = context.web_include_css + ["website_theme.css"]

	context.web_include_css = bootstrap + context.web_include_css

def get_active_theme():
	website_theme = dataent.db.get_value("Website Settings", "Website Settings", "website_theme")
	if website_theme:
		try:
			return dataent.get_doc("Website Theme", website_theme)
		except dataent.DoesNotExistError:
			pass
