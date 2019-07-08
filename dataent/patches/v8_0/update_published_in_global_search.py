from __future__ import unicode_literals
import dataent

def execute():
	from dataent.website.router import get_doctypes_with_web_view
	from dataent.utils.global_search import rebuild_for_doctype

	for doctype in get_doctypes_with_web_view():
		try:
			rebuild_for_doctype(doctype)
		except dataent.DoesNotExistError:
			pass
