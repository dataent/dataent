# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# model __init__.py
from __future__ import unicode_literals
import dataent


no_value_fields = ('Section Break', 'Column Break', 'HTML', 'Table', 'Button', 'Image',
	'Fold', 'Heading')
display_fieldtypes = ('Section Break', 'Column Break', 'HTML', 'Button', 'Image', 'Fold', 'Heading')
default_fields = ('doctype','name','owner','creation','modified','modified_by',
	'parent','parentfield','parenttype','idx','docstatus')
optional_fields = ("_user_tags", "_comments", "_assign", "_liked_by", "_seen")
core_doctypes_list = ('DocType', 'DocField', 'DocPerm', 'User', 'Role', 'Has Role',
	'Page', 'Module Def', 'Print Format', 'Report', 'Customize Form',
	'Customize Form Field', 'Property Setter', 'Custom Field', 'Custom Script')

def copytables(srctype, src, srcfield, tartype, tar, tarfield, srcfields, tarfields=[]):
	if not tarfields:
		tarfields = srcfields
	l = []
	data = src.get(srcfield)
	for d in data:
		newrow = tar.append(tarfield)
		newrow.idx = d.idx

		for i in range(len(srcfields)):
			newrow.set(tarfields[i], d.get(srcfields[i]))

		l.append(newrow)
	return l

def db_exists(dt, dn):
	return dataent.db.exists(dt, dn)

def delete_fields(args_dict, delete=0):
	"""
		Delete a field.
		* Deletes record from `tabDocField`
		* If not single doctype: Drops column from table
		* If single, deletes record from `tabSingles`

		args_dict = { dt: [field names] }
	"""
	import dataent.utils
	for dt in list(args_dict):
		fields = args_dict[dt]
		if not fields: continue

		dataent.db.sql("""\
			DELETE FROM `tabDocField`
			WHERE parent=%s AND fieldname IN (%s)
		""" % ('%s', ", ".join(['"' + f + '"' for f in fields])), dt)

		# Delete the data / column only if delete is specified
		if not delete: continue

		if dataent.db.get_value("DocType", dt, "issingle"):
			dataent.db.sql("""\
				DELETE FROM `tabSingles`
				WHERE doctype=%s AND field IN (%s)
			""" % ('%s', ", ".join(['"' + f + '"' for f in fields])), dt)
		else:
			existing_fields = dataent.db.sql("desc `tab%s`" % dt)
			existing_fields = existing_fields and [e[0] for e in existing_fields] or []
			query = "ALTER TABLE `tab%s` " % dt + \
				", ".join(["DROP COLUMN `%s`" % f for f in fields if f in existing_fields])
			dataent.db.commit()
			dataent.db.sql(query)
