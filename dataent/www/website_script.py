# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.utils import strip
from dataent.website.doctype.website_theme.website_theme import get_active_theme

no_sitemap = 1
base_template_path = "templates/www/website_script.js"

def get_context(context):
	context.javascript = dataent.db.get_single_value('Website Script',
		'javascript') or ""

	theme = get_active_theme()
	js = strip(theme and theme.js or "")
	if js:
		context.javascript += "\n" + js

	if not dataent.conf.developer_mode:
		context["google_analytics_id"] = (dataent.db.get_single_value("Website Settings", "google_analytics_id")
			or dataent.conf.get("google_analytics_id"))
