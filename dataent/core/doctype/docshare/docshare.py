# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent import _
from dataent.utils import get_fullname

exclude_from_linked_with = True

class DocShare(Document):
	no_feed_on_delete = True

	def validate(self):
		self.validate_user()
		self.check_share_permission()
		self.cascade_permissions_downwards()
		self.get_doc().run_method("validate_share", self)

	def cascade_permissions_downwards(self):
		if self.share or self.write:
			self.read = 1

	def get_doc(self):
		if not getattr(self, "_doc", None):
			self._doc = dataent.get_doc(self.share_doctype, self.share_name)
		return self._doc

	def validate_user(self):
		if self.everyone:
			self.user = None
		elif not self.user:
			dataent.throw(_("User is mandatory for Share"), dataent.MandatoryError)

	def check_share_permission(self):
		if (not self.flags.ignore_share_permission and
			not dataent.has_permission(self.share_doctype, "share", self.get_doc())):

			dataent.throw(_('You need to have "Share" permission'), dataent.PermissionError)

	def after_insert(self):
		doc = self.get_doc()
		owner = get_fullname(self.owner)

		if self.everyone:
			doc.add_comment("Shared", _("{0} shared this document with everyone").format(owner))
		else:
			doc.add_comment("Shared", _("{0} shared this document with {1}").format(owner, get_fullname(self.user)))

	def on_trash(self):
		if not self.flags.ignore_share_permission:
			self.check_share_permission()

		self.get_doc().add_comment("Unshared",
			_("{0} un-shared this document with {1}").format(get_fullname(self.owner), get_fullname(self.user)))

def on_doctype_update():
	"""Add index in `tabDocShare` for `(user, share_doctype)`"""
	dataent.db.add_index("DocShare", ["user", "share_doctype"])
	dataent.db.add_index("DocShare", ["share_doctype", "share_name"])
