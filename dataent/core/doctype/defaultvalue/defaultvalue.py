# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

from dataent.model.document import Document

class DefaultValue(Document):
	pass

def on_doctype_update():
	"""Create indexes for `tabDefaultValue` on `(parent, defkey)`"""
	if not dataent.db.sql("""show index from `tabDefaultValue`
		where Key_name="defaultvalue_parent_defkey_index" """):
		dataent.db.commit()
		dataent.db.sql("""alter table `tabDefaultValue`
			add index defaultvalue_parent_defkey_index(parent, defkey)""")

	if not dataent.db.sql("""show index from `tabDefaultValue`
		where Key_name="defaultvalue_parent_parenttype_index" """):
		dataent.db.commit()
		dataent.db.sql("""alter table `tabDefaultValue`
			add index defaultvalue_parent_parenttype_index(parent, parenttype)""")
