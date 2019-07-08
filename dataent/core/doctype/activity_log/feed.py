# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: See license.txt

from __future__ import unicode_literals
import dataent
import dataent.permissions
from dataent.utils import get_fullname
from dataent import _
from dataent.core.doctype.activity_log.activity_log import add_authentication_log
from six import string_types

def update_feed(doc, method=None):
	if dataent.flags.in_patch or dataent.flags.in_install or dataent.flags.in_import:
		return

	if doc._action!="save" or doc.flags.ignore_feed:
		return

	if doc.doctype == "Activity Log" or doc.meta.issingle:
		return

	if hasattr(doc, "get_feed"):
		feed = doc.get_feed()

		if feed:
			if isinstance(feed, string_types):
				feed = {"subject": feed}

			feed = dataent._dict(feed)
			doctype = feed.doctype or doc.doctype
			name = feed.name or doc.name

			# delete earlier feed
			dataent.db.sql("""delete from `tabActivity Log`
				where
					reference_doctype=%s and reference_name=%s
					and link_doctype=%s""", (doctype, name,feed.link_doctype))
			dataent.get_doc({
				"doctype": "Activity Log",
				"reference_doctype": doctype,
				"reference_name": name,
				"subject": feed.subject,
				"full_name": get_fullname(doc.owner),
				"reference_owner": dataent.db.get_value(doctype, name, "owner"),
				"link_doctype": feed.link_doctype,
				"link_name": feed.link_name
			}).insert(ignore_permissions=True)

def login_feed(login_manager):
	if login_manager.user != "Guest":
		subject = _("{0} logged in").format(get_fullname(login_manager.user))
		add_authentication_log(subject, login_manager.user)

def logout_feed(user, reason):
	if user and user != "Guest":
		subject = _("{0} logged out: {1}").format(get_fullname(user), dataent.bold(reason))
		add_authentication_log(subject, user, operation="Logout")

def get_feed_match_conditions(user=None, force=True):
	if not user: user = dataent.session.user

	conditions = ['`tabCommunication`.owner="{user}" or `tabCommunication`.reference_owner="{user}"'.format(user=dataent.db.escape(user))]

	user_permissions = dataent.permissions.get_user_permissions(user)
	can_read = dataent.get_user().get_can_read()

	can_read_doctypes = ['"{}"'.format(doctype) for doctype in
		list(set(can_read) - set(list(user_permissions)))]

	if can_read_doctypes:
		conditions += ["""(`tabCommunication`.reference_doctype is null
			or `tabCommunication`.reference_doctype = ''
			or `tabCommunication`.reference_doctype in ({}))""".format(", ".join(can_read_doctypes))]

		if user_permissions:
			can_read_docs = []
			for doctype, obj in user_permissions.items():
				for n in obj:
					can_read_docs.append('"{}|{}"'.format(doctype, dataent.db.escape(n.get('doc', ''))))

			if can_read_docs:
				conditions.append("concat_ws('|', `tabCommunication`.reference_doctype, `tabCommunication`.reference_name) in ({})".format(
					", ".join(can_read_docs)))

	return "(" + " or ".join(conditions) + ")"
