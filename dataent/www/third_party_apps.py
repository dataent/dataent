from __future__ import unicode_literals
import dataent
from dataent import _
import dataent.www.list

no_cache = 1
no_sitemap = 1

def get_context(context):
	if dataent.session.user == 'Guest':
		dataent.throw(_("You need to be logged in to access this page"), dataent.PermissionError)

	active_tokens = dataent.get_all("OAuth Bearer Token",
							filters=[["user", "=", dataent.session.user]],
							fields=["client"], distinct=True, order_by="creation")

	client_apps = []

	for token in active_tokens:
		creation = get_first_login(token.client)
		app = {
			"name": token.get("client"),
			"app_name": dataent.db.get_value("OAuth Client", token.get("client"), "app_name"),
			"creation": creation
		}
		client_apps.append(app)

	app = None
	if "app" in dataent.form_dict:
		app = dataent.get_doc("OAuth Client", dataent.form_dict.app)
		app = app.__dict__
		app["client_secret"] = None

	if app:
		context.app = app

	context.apps = client_apps
	context.show_sidebar = True

def get_first_login(client):
	login_date = dataent.get_all("OAuth Bearer Token",
		filters=[["user", "=", dataent.session.user], ["client", "=", client]],
		fields=["creation"], order_by="creation", limit=1)

	login_date = login_date[0].get("creation") if login_date and len(login_date) > 0 else None

	return login_date

@dataent.whitelist()
def delete_client(client_id):
	active_client_id_tokens = dataent.get_all("OAuth Bearer Token", filters=[["user", "=", dataent.session.user], ["client","=", client_id]])
	for token in active_client_id_tokens:
		dataent.delete_doc("OAuth Bearer Token", token.get("name"),  ignore_permissions=True)