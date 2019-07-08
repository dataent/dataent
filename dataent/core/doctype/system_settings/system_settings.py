# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.model.document import Document
from dataent.model import no_value_fields
from dataent.translate import set_default_language
from dataent.utils import cint
from dataent.utils.momentjs import get_all_timezones
from dataent.twofactor import toggle_two_factor_auth

class SystemSettings(Document):
	def validate(self):
		enable_password_policy = cint(self.enable_password_policy) and True or False
		minimum_password_score = cint(getattr(self, 'minimum_password_score', 0)) or 0
		if enable_password_policy and minimum_password_score <= 0:
			dataent.throw(_("Please select Minimum Password Score"))
		elif not enable_password_policy:
			self.minimum_password_score = ""

		for key in ("session_expiry", "session_expiry_mobile"):
			if self.get(key):
				parts = self.get(key).split(":")
				if len(parts)!=2 or not (cint(parts[0]) or cint(parts[1])):
					dataent.throw(_("Session Expiry must be in format {0}").format("hh:mm"))

		if self.enable_two_factor_auth:
			if self.two_factor_method=='SMS':
				if not dataent.db.get_value('SMS Settings', None, 'sms_gateway_url'):
					dataent.throw(_('Please setup SMS before setting it as an authentication method, via SMS Settings'))
			toggle_two_factor_auth(True, roles=['All'])
		else:
			self.bypass_2fa_for_retricted_ip_users = 0
			self.bypass_restrict_ip_check_if_2fa_enabled = 0

	def on_update(self):
		for df in self.meta.get("fields"):
			if df.fieldtype not in no_value_fields:
				dataent.db.set_default(df.fieldname, self.get(df.fieldname))

		if self.language:
			set_default_language(self.language)

		dataent.cache().delete_value('system_settings')
		dataent.cache().delete_value('time_zone')
		dataent.local.system_settings = {}

@dataent.whitelist()
def load():
	if not "System Manager" in dataent.get_roles():
		dataent.throw(_("Not permitted"), dataent.PermissionError)

	all_defaults = dataent.db.get_defaults()
	defaults = {}

	for df in dataent.get_meta("System Settings").get("fields"):
		if df.fieldtype in ("Select", "Data"):
			defaults[df.fieldname] = all_defaults.get(df.fieldname)

	return {
		"timezones": get_all_timezones(),
		"defaults": defaults
	}
