# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
	if not dataent.db.exists('DocType', 'Has Role'):
		dataent.rename_doc('DocType', 'Page Role', 'Has Role')
	reload_doc()
	set_ref_doctype_roles_to_report()
	copy_user_roles_to_has_roles()
	remove_doctypes()

def reload_doc():
	dataent.reload_doc("core", 'doctype', "page")
	dataent.reload_doc("core", 'doctype', "report")
	dataent.reload_doc("core", 'doctype', "user")
	dataent.reload_doc("core", 'doctype', "has_role")
	
def set_ref_doctype_roles_to_report():
	for data in dataent.get_all('Report', fields=["name"]):
		doc = dataent.get_doc('Report', data.name)
		if dataent.db.exists("DocType", doc.ref_doctype):
			try:
				doc.set_doctype_roles()
				for row in doc.roles:
					row.db_update()
			except:
				pass

def copy_user_roles_to_has_roles():
	if dataent.db.exists('DocType', 'UserRole'):
		for data in dataent.get_all('User', fields = ["name"]):
			doc = dataent.get_doc('User', data.name)
			doc.set('roles',[])
			for args in dataent.get_all('UserRole', fields = ["role"],
				filters = {'parent': data.name, 'parenttype': 'User'}):
				doc.append('roles', {
					'role': args.role
				})
			for role in doc.roles:
				role.db_update()

def remove_doctypes():
	for doctype in ['UserRole', 'Event Role']:
		if dataent.db.exists('DocType', doctype):
			dataent.delete_doc('DocType', doctype)