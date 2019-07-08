# Copyright (c) 2017, Dataent and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.utils import validate_email_add

def execute():
	''' update/delete the email group member with the wrong email '''

	email_group_members = dataent.get_all("Email Group Member", fields=["name", "email"])
	for member in email_group_members:
		validated_email = validate_email_add(member.email)
		if (validated_email==member.email):
			pass
		else:
			try:
				dataent.db.set_value("Email Group Member", member.name, "email", validated_email)
			except Exception:
				dataent.delete_doc(doctype="Email Group Member", name=member.name, force=1, ignore_permissions=True)