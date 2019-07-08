# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype('Print Format')
	dataent.db.sql(""" 
		update 
			`tabPrint Format` 
		set 
			align_labels_right = 0, line_breaks = 0, show_section_headings = 0 
		where 
			custom_format = 1
		""")
