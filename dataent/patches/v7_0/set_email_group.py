# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("email", "doctype", "email_group_member")
	if "newsletter_list" in dataent.db.get_table_columns("Email Group Member"):
		dataent.db.sql("""update `tabEmail Group Member` set email_group = newsletter_list 
			where email_group is null or email_group = ''""")