# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.translate import send_translations

@dataent.whitelist()
def get(name):
	"""
	   Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = dataent.get_doc('Page', name)
	if page.is_permitted():
		page.load_assets()
		docs = dataent._dict(page.as_dict())
		if getattr(page, '_dynamic_page', None):
			docs['_dynamic_page'] = 1

		return docs
	else:
		dataent.response['403'] = 1
		raise dataent.PermissionError('No read permission for Page %s' %(page.title or name))


@dataent.whitelist(allow_guest=True)
def getpage():
	"""
	   Load the page from `dataent.form` and send it via `dataent.response`
	"""
	page = dataent.form_dict.get('name')
	doc = get(page)

	# load translations
	if dataent.lang != "en":
		send_translations(dataent.get_lang_dict("page", page))

	dataent.response.docs.append(doc)

def has_permission(page):
	if dataent.session.user == "Administrator" or "System Manager" in dataent.get_roles():
		return True

	page_roles = [d.role for d in page.get("roles")]
	if page_roles:
		if dataent.session.user == "Guest" and "Guest" not in page_roles:
			return False
		elif not set(page_roles).intersection(set(dataent.get_roles())):
			# check if roles match
			return False

	if not dataent.has_permission("Page", ptype="read", doc=page):
		# check if there are any user_permissions
		return False
	else:
		# hack for home pages! if no Has Roles, allow everyone to see!
		return True
