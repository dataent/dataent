# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	for d in dataent.get_all("Property Setter", fields=["name", "doc_type"],
		filters={"doctype_or_field": "DocField", "property": "allow_on_submit", "value": "1"}):
		dataent.delete_doc("Property Setter", d.name)
		dataent.clear_cache(doctype=d.doc_type)
