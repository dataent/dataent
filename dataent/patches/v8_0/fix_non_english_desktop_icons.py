# Copyright (c) 2017, Dataent and Contributors
# License: GNU General Public License v3. See license.txt
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import dataent
from dataent.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache

def execute():	
	dataent.db.sql("""
		update `tabDesktop Icon`
		set module_name=_doctype, label=_doctype
		where type = 'link' and _doctype != label and link like 'List/%'
	""")