# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent import _

class OAuthProviderSettings(Document):
	pass

def get_oauth_settings():
	"""Returns oauth settings"""
	out = dataent._dict({
		"skip_authorization" : dataent.db.get_value("OAuth Provider Settings", None, "skip_authorization")
	})

	return out