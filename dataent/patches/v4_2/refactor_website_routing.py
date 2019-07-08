from __future__ import unicode_literals
import dataent

def execute():
	# clear all static web pages
	dataent.delete_doc("DocType", "Website Route", force=1)
	dataent.delete_doc("Page", "sitemap-browser", force=1)
	dataent.db.sql("drop table if exists `tabWebsite Route`")
