# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
import dataent.defaults
from dataent.modules.import_file import get_file_path, read_doc_from_file
from dataent.translate import send_translations
from dataent.core.doctype.doctype.doctype import (clear_permissions_cache,
	validate_permissions_for_doctype)
from dataent.permissions import (reset_perms, get_linked_doctypes, get_all_perms,
	setup_custom_perms, add_permission, update_permission_property)

not_allowed_in_permission_manager = ["DocType", "Patch Log", "Module Def", "Transaction Log"]

@dataent.whitelist()
def get_roles_and_doctypes():
	dataent.only_for("System Manager")
	send_translations(dataent.get_lang_dict("doctype", "DocPerm"))

	active_domains = dataent.get_active_domains()

	doctypes = dataent.get_all("DocType", filters={
		"istable": 0,
		"name": ("not in", ",".join(not_allowed_in_permission_manager)),
	}, or_filters={
		"ifnull(restrict_to_domain, '')": "",
		"restrict_to_domain": ("in", active_domains)
	}, fields=["name"])

	roles = dataent.get_all("Role", filters={
		"name": ("not in", "Administrator"),
		"disabled": 0,
	}, or_filters={
		"ifnull(restrict_to_domain, '')": "",
		"restrict_to_domain": ("in", active_domains)
	}, fields=["name"])

	doctypes_list = [ {"label":_(d.get("name")), "value":d.get("name")} for d in doctypes]
	roles_list = [ {"label":_(d.get("name")), "value":d.get("name")} for d in roles]

	return {
		"doctypes": sorted(doctypes_list, key=lambda d: d['label']),
		"roles": sorted(roles_list, key=lambda d: d['label'])
	}

@dataent.whitelist()
def get_permissions(doctype=None, role=None):
	dataent.only_for("System Manager")
	if role:
		out = get_all_perms(role)
		if doctype:
			out = [p for p in out if p.parent == doctype]
	else:
		out = dataent.get_all('Custom DocPerm', fields='*', filters=dict(parent = doctype), order_by="permlevel")
		if not out:
			out = dataent.get_all('DocPerm', fields='*', filters=dict(parent = doctype), order_by="permlevel")

	linked_doctypes = {}
	for d in out:
		if not d.parent in linked_doctypes:
			linked_doctypes[d.parent] = get_linked_doctypes(d.parent)
		d.linked_doctypes = linked_doctypes[d.parent]
		meta = dataent.get_meta(d.parent)
		if meta:
			d.is_submittable = meta.is_submittable

	return out

@dataent.whitelist()
def add(parent, role, permlevel):
	dataent.only_for("System Manager")
	add_permission(parent, role, permlevel)

@dataent.whitelist()
def update(doctype, role, permlevel, ptype, value=None):
	dataent.only_for("System Manager")
	out = update_permission_property(doctype, role, permlevel, ptype, value)
	return 'refresh' if out else None

@dataent.whitelist()
def remove(doctype, role, permlevel):
	dataent.only_for("System Manager")
	setup_custom_perms(doctype)

	name = dataent.get_value('Custom DocPerm', dict(parent=doctype, role=role, permlevel=permlevel))

	dataent.db.sql('delete from `tabCustom DocPerm` where name=%s', name)
	if not dataent.get_all('Custom DocPerm', dict(parent=doctype)):
		dataent.throw(_('There must be atleast one permission rule.'), title=_('Cannot Remove'))

	validate_permissions_for_doctype(doctype, for_remove=True)

@dataent.whitelist()
def reset(doctype):
	dataent.only_for("System Manager")
	reset_perms(doctype)
	clear_permissions_cache(doctype)

@dataent.whitelist()
def get_users_with_role(role):
	dataent.only_for("System Manager")

	return [p[0] for p in dataent.db.sql("""select distinct tabUser.name
		from `tabHas Role`, tabUser where
			`tabHas Role`.role=%s
			and tabUser.name != "Administrator"
			and `tabHas Role`.parent = tabUser.name
			and tabUser.enabled=1""", role)]

@dataent.whitelist()
def get_standard_permissions(doctype):
	dataent.only_for("System Manager")
	meta = dataent.get_meta(doctype)
	if meta.custom:
		doc = dataent.get_doc('DocType', doctype)
		return [p.as_dict() for p in doc.permissions]
	else:
		# also used to setup permissions via patch
		path = get_file_path(meta.module, "DocType", doctype)
		return read_doc_from_file(path).get("permissions")
