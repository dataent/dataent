from __future__ import unicode_literals
import dataent, json

def execute():
	dataent.clear_cache()
	installed = dataent.get_installed_apps()
	if "webnotes" in installed:
		installed.remove("webnotes")
	if "dataent" not in installed:
		installed = ["dataent"] + installed
	dataent.db.set_global("installed_apps", json.dumps(installed))
	dataent.clear_cache()
