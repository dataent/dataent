# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
import dataent.www.list

no_cache = 1
no_sitemap = 1

def get_context(context):
	if dataent.session.user=='Guest':
		dataent.throw(_("You need to be logged in to access this page"), dataent.PermissionError)

	context.show_sidebar=True