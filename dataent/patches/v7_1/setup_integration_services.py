from __future__ import unicode_literals
import dataent
from dataent.exceptions import DataError
from dataent.utils.password import get_decrypted_password
from dataent.utils import cstr
import os

app_list = [
	{"app_name": "razorpay_integration", "service_name": "Razorpay", "doctype": "Razorpay Settings", "remove": True},
	{"app_name": "paypal_integration", "service_name": "PayPal", "doctype": "PayPal Settings", "remove": True},
	{"app_name": "dataent", "service_name": "Dropbox", "doctype": "Dropbox Backup", "remove": False}
]

def execute():
	installed_apps = dataent.get_installed_apps()

	for app_details in app_list:
		if app_details["app_name"] in installed_apps:
			settings = get_app_settings(app_details)
			if app_details["remove"]:
				uninstall_app(app_details["app_name"])

			try:
				setup_integration_service(app_details, settings)
			except DataError:
				pass

	dataent.delete_doc("DocType", "Dropbox Backup")

def setup_integration_service(app_details, settings=None):
	if not settings:
		return

	setup_service_settings(app_details["service_name"], settings)

	doc_path = dataent.get_app_path("dataent", "integration_broker", "doctype",
		"integration_service", "integration_service.json")

	if not os.path.exists(doc_path):
		return

	dataent.reload_doc("integration_broker", "doctype", "integration_service")

	if dataent.db.exists("Integration Service", app_details["service_name"]):
		integration_service = dataent.get_doc("Integration Service", app_details["service_name"])
	else:
		integration_service = dataent.new_doc("Integration Service")
		integration_service.service = app_details["service_name"]

	integration_service.enabled = 1
	integration_service.flags.ignore_mandatory = True
	integration_service.save(ignore_permissions=True)

def get_app_settings(app_details):
	parameters = {}
	doctype = docname = app_details["doctype"]

	app_settings = get_parameters(app_details)
	if app_settings:
		settings = app_settings["settings"]
		dataent.reload_doc("integrations", "doctype", "{0}_settings".format(app_details["service_name"].lower()))
		controller = dataent.get_meta("{0} Settings".format(app_details["service_name"]))

		for d in controller.fields:
			if settings.get(d.fieldname):
				if ''.join(set(cstr(settings.get(d.fieldname)))) == '*':
					setattr(settings, d.fieldname, get_decrypted_password(doctype, docname, d.fieldname, raise_exception=True))

				parameters.update({d.fieldname : settings.get(d.fieldname)})

	return parameters

def uninstall_app(app_name):
	from dataent.installer import remove_from_installed_apps
	remove_from_installed_apps(app_name)

def get_parameters(app_details):
	if app_details["service_name"] == "Razorpay":
		return {"settings": dataent.get_doc(app_details["doctype"])}

	elif app_details["service_name"] == "PayPal":
		if dataent.conf.paypal_username and dataent.conf.paypal_password and dataent.conf.paypal_signature:
			return {
				"settings": {
					"api_username": dataent.conf.paypal_username,
					"api_password": dataent.conf.paypal_password,
					"signature": dataent.conf.paypal_signature
				}
			}
		else:
			return {"settings": dataent.get_doc(app_details["doctype"])}

	elif app_details["service_name"] == "Dropbox":
		doc = dataent.db.get_value(app_details["doctype"], None,
			["dropbox_access_key", "dropbox_access_secret", "upload_backups_to_dropbox"], as_dict=1)

		if not doc:
			return

		if not (dataent.conf.dropbox_access_key and dataent.conf.dropbox_secret_key):
			return

		return {
			"settings": {
				"app_access_key": dataent.conf.dropbox_access_key,
				"app_secret_key": dataent.conf.dropbox_secret_key,
				"dropbox_access_key": doc.dropbox_access_key,
				"dropbox_access_secret": doc.dropbox_access_secret,
				"backup_frequency": doc.upload_backups_to_dropbox,
				"enabled": doc.send_backups_to_dropbox
			}
		}

def setup_service_settings(service_name, settings):
	service_doc = dataent.get_doc("{0} Settings".format(service_name))
	service_doc.update(settings)
	service_doc.flags.ignore_mandatory = True
	service_doc.save(ignore_permissions=True)