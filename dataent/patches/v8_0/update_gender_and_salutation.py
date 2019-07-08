# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors

from __future__ import unicode_literals
import dataent
from dataent.desk.page.setup_wizard.install_fixtures import update_genders_and_salutations

def execute():
	dataent.db.set_value("DocType", "Contact", "module", "Contacts")
	dataent.db.set_value("DocType", "Address", "module", "Contacts")
	dataent.db.set_value("DocType", "Address Template", "module", "Contacts")
	dataent.reload_doc('contacts', 'doctype', 'gender')
	dataent.reload_doc('contacts', 'doctype', 'salutation')

	update_genders_and_salutations()