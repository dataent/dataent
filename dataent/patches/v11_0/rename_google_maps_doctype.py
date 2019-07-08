from __future__ import unicode_literals
import dataent
from dataent.model.rename_doc import rename_doc

def execute():
	if dataent.db.exists("DocType","Google Maps") and not dataent.db.exists("DocType","Google Maps Settings"):
		rename_doc('DocType', 'Google Maps', 'Google Maps Settings')
		dataent.reload_doc('integrations', 'doctype', 'google_maps_settings')