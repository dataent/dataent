# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent.utils import get_source_value

class DataMigrationMapping(Document):
	def get_filters(self):
		if self.condition:
			return dataent.safe_eval(self.condition, dict(dataent=dataent))

	def get_fields(self):
		fields = []
		for f in self.fields:
			if not (f.local_fieldname[0] in ('"', "'") or f.local_fieldname.startswith('eval:')):
				fields.append(f.local_fieldname)

		if dataent.db.has_column(self.local_doctype, self.migration_id_field):
			fields.append(self.migration_id_field)

		if 'name' not in fields:
			fields.append('name')

		return fields

	def get_mapped_record(self, doc):
		'''Build a mapped record using information from the fields table'''
		mapped = dataent._dict()

		key_fieldname = 'remote_fieldname'
		value_fieldname = 'local_fieldname'

		if self.mapping_type == 'Pull':
			key_fieldname, value_fieldname = value_fieldname, key_fieldname

		for field_map in self.fields:
			key = get_source_value(field_map, key_fieldname)

			if not field_map.is_child_table:
				# field to field mapping
				value = get_value_from_fieldname(field_map, value_fieldname, doc)
			else:
				# child table mapping
				mapping_name = field_map.child_table_mapping
				value = get_mapped_child_records(mapping_name,
					doc.get(get_source_value(field_map, value_fieldname)))

			mapped[key] = value

		return mapped

def get_mapped_child_records(mapping_name, child_docs):
	mapped_child_docs = []
	mapping = dataent.get_doc('Data Migration Mapping', mapping_name)
	for child_doc in child_docs:
		mapped_child_docs.append(mapping.get_mapped_record(child_doc))

	return mapped_child_docs

def get_value_from_fieldname(field_map, fieldname_field, doc):
	field_name = get_source_value(field_map, fieldname_field)

	if field_name.startswith('eval:'):
		value = dataent.safe_eval(field_name[5:], dict(dataent=dataent))
	elif field_name[0] in ('"', "'"):
		value = field_name[1:-1]
	else:
		value = get_source_value(doc, field_name)
	return value
