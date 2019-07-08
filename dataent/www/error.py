# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function
import dataent

no_cache = 1
no_sitemap = 1

def get_context(context):
	if dataent.flags.in_migrate: return
	print(dataent.get_traceback().encode("utf-8"))
	return {"error": dataent.get_traceback().replace("<", "&lt;").replace(">", "&gt;") }
