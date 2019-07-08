# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent

from dataent import throw, _
from dataent.utils import cstr

from dataent.model.document import Document
from jinja2 import TemplateSyntaxError
from dataent.utils.user import is_website_user
from dataent.model.naming import make_autoname
from dataent.core.doctype.dynamic_link.dynamic_link import deduplicate_dynamic_links
from six import iteritems, string_types
from past.builtins import cmp
from dataent.contacts.address_and_contact import set_link_title

import functools


class Address(Document):
	def __setup__(self):
		self.flags.linked = False

	def autoname(self):
		if not self.address_title:
			if self.links:
				self.address_title = self.links[0].link_name

		if self.address_title:
			self.name = (cstr(self.address_title).strip() + "-" + cstr(_(self.address_type)).strip())
			if dataent.db.exists("Address", self.name):
				self.name = make_autoname(cstr(self.address_title).strip() + "-" +
					cstr(self.address_type).strip() + "-.#")
		else:
			throw(_("Address Title is mandatory."))

	def validate(self):
		self.link_address()
		self.validate_reference()
		set_link_title(self)
		deduplicate_dynamic_links(self)

	def link_address(self):
		"""Link address based on owner"""
		if not self.links and not self.is_your_company_address:
			contact_name = dataent.db.get_value("Contact", {"email_id": self.owner})
			if contact_name:
				contact = dataent.get_cached_doc('Contact', contact_name)
				for link in contact.links:
					self.append('links', dict(link_doctype=link.link_doctype, link_name=link.link_name))
				return True

		return False

	def validate_reference(self):
		if self.is_your_company_address:
			if not [row for row in self.links if row.link_doctype == "Company"]:
				dataent.throw(_("Company is mandatory, as it is your company address"))

			# removing other links
			to_remove = [row for row in self.links if row.link_doctype != "Company"]
			[ self.remove(row) for row in to_remove ]

	def get_display(self):
		return get_address_display(self.as_dict())

	def has_link(self, doctype, name):
		for link in self.links:
			if link.link_doctype==doctype and link.link_name== name:
				return True

	def has_common_link(self, doc):
		reference_links = [(link.link_doctype, link.link_name) for link in doc.links]
		for link in self.links:
			if (link.link_doctype, link.link_name) in reference_links:
				return True

		return False

@dataent.whitelist()
def get_default_address(doctype, name, sort_key='is_primary_address'):
	'''Returns default Address name for the given doctype, name'''
	if sort_key not in ['is_shipping_address', 'is_primary_address']:
		return None

	out = dataent.db.sql(""" SELECT
			addr.name, addr.%s
		FROM
			`tabAddress` addr, `tabDynamic Link` dl
		WHERE
			dl.parent = addr.name and dl.link_doctype = %s and
			dl.link_name = %s and ifnull(addr.disabled, 0) = 0
		""" %(sort_key, '%s', '%s'), (doctype, name))

	if out:
		return sorted(out, key = functools.cmp_to_key(lambda x,y: cmp(y[1], x[1])))[0][0]
	else:
		return None


@dataent.whitelist()
def get_address_display(address_dict):
	if not address_dict:
		return

	if not isinstance(address_dict, dict):
		address_dict = dataent.db.get_value("Address", address_dict, "*", as_dict=True, cache=True) or {}

	name, template = get_address_templates(address_dict)

	try:
		return dataent.render_template(template, address_dict)
	except TemplateSyntaxError:
		dataent.throw(_("There is an error in your Address Template {0}").format(name))


def get_territory_from_address(address):
	"""Tries to match city, state and country of address to existing territory"""
	if not address:
		return

	if isinstance(address, string_types):
		address = dataent.get_cached_doc("Address", address)

	territory = None
	for fieldname in ("city", "state", "country"):
		if address.get(fieldname):
			territory = dataent.db.get_value("Territory", address.get(fieldname))
			if territory:
				break

	return territory

def get_list_context(context=None):
	return {
		"title": _("Addresses"),
		"get_list": get_address_list,
		"row_template": "templates/includes/address_row.html",
		'no_breadcrumbs': True,
	}

def get_address_list(doctype, txt, filters, limit_start, limit_page_length = 20, order_by = None):
    from dataent.www.list import get_list
    user = dataent.session.user
    ignore_permissions = False
    if is_website_user():
        if not filters: filters = []
        add_name = []
        contact = dataent.db.sql("""
			select
				address.name
			from
				`tabDynamic Link` as link
			join
				`tabAddress` as address on link.parent = address.name
			where
				link.parenttype = 'Address' and
				link_name in(
				   select
					   link.link_name from `tabContact` as contact
				   join
					   `tabDynamic Link` as link on contact.name = link.parent
				   where
					   contact.user = %s)""",(user))
        for c in contact:
            add_name.append(c[0])
        filters.append(("Address", "name", "in", add_name))
        ignore_permissions = True

    return get_list(doctype, txt, filters, limit_start, limit_page_length, ignore_permissions=ignore_permissions)

def has_website_permission(doc, ptype, user, verbose=False):
	"""Returns true if there is a related lead or contact related to this document"""
	contact_name = dataent.db.get_value("Contact", {"email_id": dataent.session.user})
	if contact_name:
		contact = dataent.get_doc('Contact', contact_name)
		return contact.has_common_link(doc)

		lead_name = dataent.db.get_value("Lead", {"email_id": dataent.session.user})
		if lead_name:
			return doc.has_link('Lead', lead_name)

	return False

def get_address_templates(address):
	result = dataent.db.get_value("Address Template", \
		{"country": address.get("country")}, ["name", "template"])

	if not result:
		result = dataent.db.get_value("Address Template", \
			{"is_default": 1}, ["name", "template"])

	if not result:
		dataent.throw(_("No default Address Template found. Please create a new one from Setup > Printing and Branding > Address Template."))
	else:
		return result

@dataent.whitelist()
def get_shipping_address(company, address = None):
	filters = [
		["Dynamic Link", "link_doctype", "=", "Company"],
		["Dynamic Link", "link_name", "=", company],
		["Address", "is_your_company_address", "=", 1]
	]
	fields = ["*"]
	if address and dataent.db.get_value('Dynamic Link',
		{'parent': address, 'link_name': company}):
		filters.append(["Address", "name", "=", address])

	address = dataent.get_all("Address", filters=filters, fields=fields) or {}

	if address:
		address_as_dict = address[0]
		name, address_template = get_address_templates(address_as_dict)
		return address_as_dict.get("name"), dataent.render_template(address_template, address_as_dict)

def get_company_address(company):
	ret = dataent._dict()
	ret.company_address = get_default_address('Company', company)
	ret.company_address_display = get_address_display(ret.company_address)

	return ret

def address_query(doctype, txt, searchfield, start, page_len, filters):
	from dataent.desk.reportview import get_match_cond

	link_doctype = filters.pop('link_doctype')
	link_name = filters.pop('link_name')

	condition = ""
	for fieldname, value in iteritems(filters):
		condition += " and {field}={value}".format(
			field=fieldname,
			value=value
		)

	return dataent.db.sql("""select
			`tabAddress`.name, `tabAddress`.city, `tabAddress`.country
		from
			`tabAddress`, `tabDynamic Link`
		where
			`tabDynamic Link`.parent = `tabAddress`.name and
			`tabDynamic Link`.parenttype = 'Address' and
			`tabDynamic Link`.link_doctype = %(link_doctype)s and
			`tabDynamic Link`.link_name = %(link_name)s and
			ifnull(`tabAddress`.disabled, 0) = 0 and
			`tabAddress`.`{key}` like %(txt)s
			{mcond} {condition}
		order by
			if(locate(%(_txt)s, `tabAddress`.name), locate(%(_txt)s, `tabAddress`.name), 99999),
			`tabAddress`.idx desc, `tabAddress`.name
		limit %(start)s, %(page_len)s """.format(
			mcond=get_match_cond(doctype),
			key=dataent.db.escape(searchfield),
			condition=condition or ""),
		{
			'txt': "%%%s%%" % dataent.db.escape(txt),
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len,
			'link_name': link_name,
			'link_doctype': link_doctype
		})
