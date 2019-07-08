from __future__ import unicode_literals
import dataent

from dataent.model.utils.rename_field import rename_field
from dataent.model.meta import get_table_columns

def execute():
	tables = dataent.db.sql_list("show tables")
	if "tabUser" not in tables:
		dataent.rename_doc("DocType", "Profile", "User", force=True)

	dataent.reload_doc("website", "doctype", "blogger")

	if "profile" in get_table_columns("Blogger"):
		rename_field("Blogger", "profile", "user")
