from __future__ import unicode_literals
import dataent

def execute():
	pass
	# from dataent.website.doctype.website_template.website_template import \
	# 	get_pages_and_generators, get_template_controller
	#
	# dataent.reload_doc("website", "doctype", "website_template")
	# dataent.reload_doc("website", "doctype", "website_route")
	#
	# for app in dataent.get_installed_apps():
	# 	pages, generators = get_pages_and_generators(app)
	# 	for g in generators:
	# 		doctype = dataent.get_attr(get_template_controller(app, g["path"], g["fname"]) + ".doctype")
	# 		module = dataent.db.get_value("DocType", doctype, "module")
	# 		dataent.reload_doc(dataent.scrub(module), "doctype", dataent.scrub(doctype))
	#
	# dataent.db.sql("""update `tabBlog Category` set `title`=`name` where ifnull(`title`, '')=''""")
	# dataent.db.sql("""update `tabWebsite Route` set idx=null""")
	# for doctype in ["Blog Category", "Blog Post", "Web Page", "Website Group"]:
	# 	dataent.db.sql("""update `tab{}` set idx=null""".format(doctype))
	#
	# from dataent.website.doctype.website_template.website_template import rebuild_website_template
	# rebuild_website_template()
