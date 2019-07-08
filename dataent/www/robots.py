from __future__ import unicode_literals
import dataent

no_sitemap = 1
base_template_path = "templates/www/robots.txt"

def get_context(context):
	robots_txt = (
		dataent.db.get_single_value('Website Settings', 'robots_txt') or
		(dataent.local.conf.robots_txt and dataent.read_file(dataent.local.conf.robots_txt)) or '')

	return { 'robots_txt': robots_txt }
