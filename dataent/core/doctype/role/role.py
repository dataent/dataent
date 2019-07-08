# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

from dataent.model.document import Document

class Role(Document):
	def before_rename(self, old, new, merge=False):
		if old in ("Guest", "Administrator", "System Manager", "All"):
			dataent.throw(dataent._("Standard roles cannot be renamed"))

	def after_insert(self):
		dataent.cache().hdel('roles', 'Administrator')

	def validate(self):
		if self.disabled:
			if self.name in ("Guest", "Administrator", "System Manager", "All"):
				dataent.throw(dataent._("Standard roles cannot be disabled"))
			else:
				dataent.db.sql("delete from `tabHas Role` where role = %s", self.name)
				dataent.clear_cache()

# Get email addresses of all users that have been assigned this role
def get_emails_from_role(role):
	emails = []

	users = dataent.get_list("Has Role", filters={"role": role, "parenttype": "User"},
		fields=["parent"])

	for user in users:
		user_email, enabled = dataent.db.get_value("User", user.parent, ["email", "enabled"])
		if enabled:
			emails.append(user_email)

	return emails