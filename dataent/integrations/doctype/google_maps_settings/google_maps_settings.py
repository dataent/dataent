# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import dataent
from dataent import _
from dataent.model.document import Document


class GoogleMapsSettings(Document):
	def validate(self):
		if self.enabled:
			if not self.client_key:
				dataent.throw(_("Client key is required"))
			if not self.home_address:
				dataent.throw(_("Home Address is required"))

	def get_client(self):
		if not self.enabled:
			dataent.throw(_("Google Maps integration is not enabled"))

		import googlemaps

		try:
			client = googlemaps.Client(key=self.client_key)
		except Exception as e:
			dataent.throw(e.message)

		return client
