# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
import dataent.permissions

def execute():
	dataent.reload_doc("core", "doctype", "docperm")
	table_columns = dataent.db.get_table_columns("DocPerm")

	if "restricted" in table_columns:
		dataent.db.sql("""update `tabDocPerm` set apply_user_permissions=1 where apply_user_permissions=0
			and restricted=1""")

	if "match" in table_columns:
		dataent.db.sql("""update `tabDocPerm` set apply_user_permissions=1
			where apply_user_permissions=0 and ifnull(`match`, '')!=''""")

	# change Restriction to User Permission in tabDefaultValue
	dataent.db.sql("""update `tabDefaultValue` set parenttype='User Permission' where parenttype='Restriction'""")

	dataent.clear_cache()

