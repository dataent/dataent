# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

from dataent import _

no_sitemap = 1
no_cache = 1

def get_context(context):
	context.no_breadcrumbs = True
	context.parents = [{"name":"me", "title":_("My Account")}]
