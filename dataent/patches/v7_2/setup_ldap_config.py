from __future__ import unicode_literals
import dataent
from dataent.utils import cint

def execute():
	dataent.reload_doc("integrations", "doctype", "ldap_settings")

	if not dataent.db.exists("DocType", "Integration Service"):
		return

	if not dataent.db.exists("Integration Service", "LDAP"):
		return

	if not cint(dataent.db.get_value("Integration Service", "LDAP", 'enabled')):
		return

	import ldap
	try:
		ldap_settings = dataent.get_doc("LDAP Settings")
		ldap_settings.save(ignore_permissions=True)
	except ldap.LDAPError:
		pass
