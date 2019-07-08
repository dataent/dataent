# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import dataent, json
from dataent.model.meta import is_single
from dataent.modules import load_doctype_module
import dataent.desk.form.meta
import dataent.desk.form.load
from six import string_types
from collections import defaultdict


@dataent.whitelist()
def get_linked_docs(doctype, name, linkinfo=None, for_doctype=None):
	if isinstance(linkinfo, string_types):
		# additional fields are added in linkinfo
		linkinfo = json.loads(linkinfo)

	results = {}

	if not linkinfo:
		return results

	if for_doctype:
		links = dataent.get_doc(doctype, name).get_link_filters(for_doctype)

		if links:
			linkinfo = links

		if for_doctype in linkinfo:
			# only get linked with for this particular doctype
			linkinfo = { for_doctype: linkinfo.get(for_doctype) }
		else:
			return results

	me = dataent.db.get_value(doctype, name, ["parenttype", "parent"], as_dict=True)

	for dt, link in linkinfo.items():
		filters = []
		link["doctype"] = dt
		link_meta_bundle = dataent.desk.form.load.get_meta_bundle(dt)
		linkmeta = link_meta_bundle[0]
		if not linkmeta.get("issingle"):
			fields = [d.fieldname for d in linkmeta.get("fields", {"in_list_view":1,
				"fieldtype": ["not in", ["Image", "HTML", "Button", "Table"]]})] \
				+ ["name", "modified", "docstatus"]

			if link.get("add_fields"):
				fields += link["add_fields"]

			fields = ["`tab{dt}`.`{fn}`".format(dt=dt, fn=sf.strip()) for sf in fields if sf
				and "`tab" not in sf]

			try:
				if link.get("filters"):
					ret = dataent.get_list(doctype=dt, fields=fields, filters=link.get("filters"))

				elif link.get("get_parent"):
					if me and me.parent and me.parenttype == dt:
						ret = dataent.get_list(doctype=dt, fields=fields,
							filters=[[dt, "name", '=', me.parent]])
					else:
						ret = None

				elif link.get("child_doctype"):
					or_filters = [[link.get('child_doctype'), link_fieldnames, '=', name] for link_fieldnames in link.get("fieldname")]

					# dynamic link
					if link.get("doctype_fieldname"):
						filters.append([link.get('child_doctype'), link.get("doctype_fieldname"), "=", doctype])

					ret = dataent.get_list(doctype=dt, fields=fields, filters=filters, or_filters=or_filters, distinct=True)

				else:
					link_fieldnames = link.get("fieldname")
					if link_fieldnames:
						if isinstance(link_fieldnames, string_types): link_fieldnames = [link_fieldnames]
						or_filters = [[dt, fieldname, '=', name] for fieldname in link_fieldnames]
						# dynamic link
						if link.get("doctype_fieldname"):
							filters.append([dt, link.get("doctype_fieldname"), "=", doctype])
						ret = dataent.get_list(doctype=dt, fields=fields, filters=filters, or_filters=or_filters)

					else:
						ret = None

			except dataent.PermissionError:
				if dataent.local.message_log:
					dataent.local.message_log.pop()

				continue

			if ret:
				results[dt] = ret

	return results

@dataent.whitelist()
def get_linked_doctypes(doctype, without_ignore_user_permissions_enabled=False):
	"""add list of doctypes this doctype is 'linked' with.

	Example, for Customer:

		{"Address": {"fieldname": "customer"}..}
	"""
	if(without_ignore_user_permissions_enabled):
		return dataent.cache().hget("linked_doctypes_without_ignore_user_permissions_enabled",
			doctype, lambda: _get_linked_doctypes(doctype, without_ignore_user_permissions_enabled))
	else:
		return dataent.cache().hget("linked_doctypes", doctype, lambda: _get_linked_doctypes(doctype))

def _get_linked_doctypes(doctype, without_ignore_user_permissions_enabled=False):
	ret = {}
	# find fields where this doctype is linked
	ret.update(get_linked_fields(doctype, without_ignore_user_permissions_enabled))
	ret.update(get_dynamic_linked_fields(doctype, without_ignore_user_permissions_enabled))

	filters=[['fieldtype','=','Table'], ['options', '=', doctype]]
	if without_ignore_user_permissions_enabled: filters.append(['ignore_user_permissions', '!=', 1])
	# find links of parents
	links = dataent.get_all("DocField", fields=["parent as dt"], filters=filters)
	links+= dataent.get_all("Custom Field", fields=["dt"], filters=filters)

	for dt, in links:
		if dt in ret: continue
		ret[dt] = {"get_parent": True}

	for dt in list(ret):
		try:
			doctype_module = load_doctype_module(dt)
		except (ImportError, KeyError):
			# in case of Custom DocType
			# or in case of module rename eg. (Schools -> Education)
			continue

		if getattr(doctype_module, "exclude_from_linked_with", False):
			del ret[dt]

	return ret

def get_linked_fields(doctype, without_ignore_user_permissions_enabled=False):

	filters=[['fieldtype','=', 'Link'], ['options', '=', doctype]]
	if without_ignore_user_permissions_enabled: filters.append(['ignore_user_permissions', '!=', 1])

	# find links of parents
	links = dataent.get_all("DocField", fields=["parent", "fieldname"], filters=filters, as_list=1)
	links+= dataent.get_all("Custom Field", fields=["dt as parent", "fieldname"], filters=filters, as_list=1)

	ret = {}

	if not links: return ret

	links_dict = defaultdict(list)
	for doctype, fieldname in links:
		links_dict[doctype].append(fieldname)

	for doctype_name in links_dict:
		ret[doctype_name] = { "fieldname": links_dict.get(doctype_name) }
	table_doctypes = dataent.get_all("DocType", filters=[["istable", "=", "1"], ["name", "in", tuple(links_dict)]])
	child_filters = [['fieldtype','=', 'Table'], ['options', 'in', tuple(doctype.name for doctype in table_doctypes)]]
	if without_ignore_user_permissions_enabled: child_filters.append(['ignore_user_permissions', '!=', 1])

	# find out if linked in a child table
	for parent, options in dataent.get_all("DocField", fields=["parent", "options"], filters=child_filters, as_list=1):
		ret[parent] = { "child_doctype": options, "fieldname": links_dict[options]}
		if options in ret: del ret[options]

	return ret

def get_dynamic_linked_fields(doctype, without_ignore_user_permissions_enabled=False):
	ret = {}

	filters=[['fieldtype','=', 'Dynamic Link']]
	if without_ignore_user_permissions_enabled: filters.append(['ignore_user_permissions', '!=', 1])

	# find dynamic links of parents
	links = dataent.get_all("DocField", fields=["parent as doctype", "fieldname", "options as doctype_fieldname"], filters=filters)
	links+= dataent.get_all("Custom Field", fields=["dt as doctype", "fieldname", "options as doctype_fieldname"], filters=filters)

	for df in links:
		if is_single(df.doctype): continue

		# optimized to get both link exists and parenttype
		possible_link = dataent.db.sql("""select distinct `{doctype_fieldname}`, parenttype
			from `tab{doctype}` where `{doctype_fieldname}`=%s""".format(**df), doctype, as_dict=True)

		if not possible_link: continue

		for d in possible_link:
			# is child
			if d.parenttype:
				ret[d.parenttype] = {
					"child_doctype": df.doctype,
					"fieldname": [df.fieldname],
					"doctype_fieldname": df.doctype_fieldname
				}
			else:
				ret[df.doctype] = {
					"fieldname": [df.fieldname],
					"doctype_fieldname": df.doctype_fieldname
				}

	return ret