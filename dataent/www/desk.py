# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function

no_sitemap = 1
no_cache = 1
base_template_path = "templates/www/desk.html"

import os, re
import dataent
from dataent import _
import dataent.sessions

def get_context(context):
	if (dataent.session.user == "Guest" or
		dataent.db.get_value("User", dataent.session.user, "user_type")=="Website User"):
		dataent.throw(_("You are not permitted to access this page."), dataent.PermissionError)

	hooks = dataent.get_hooks()
	try:
		boot = dataent.sessions.get()
	except Exception as e:
		boot = dataent._dict(status='failed', error = str(e))
		print(dataent.get_traceback())

	# this needs commit
	csrf_token = dataent.sessions.get_csrf_token()

	dataent.db.commit()

	boot_json = dataent.as_json(boot)

	# remove script tags from boot
	boot_json = re.sub("\<script\>[^<]*\</script\>", "", boot_json)

	context.update({
		"no_cache": 1,
		"build_version": get_build_version(),
		"include_js": hooks["app_include_js"],
		"include_css": hooks["app_include_css"],
		"sounds": hooks["sounds"],
		"boot": boot if context.get("for_mobile") else boot_json,
		"csrf_token": csrf_token,
		"background_image": (boot.status != 'failed' and
			(boot.user.background_image or boot.default_background_image) or None),
		"google_analytics_id": dataent.conf.get("google_analytics_id"),
		"mixpanel_id": dataent.conf.get("mixpanel_id")
	})

	return context

@dataent.whitelist()
def get_desk_assets(build_version):
	"""Get desk assets to be loaded for mobile app"""
	data = get_context({"for_mobile": True})
	assets = [{"type": "js", "data": ""}, {"type": "css", "data": ""}]

	if build_version != data["build_version"]:
		# new build, send assets
		for path in data["include_js"]:
			# assets path shouldn't start with /
			# as it points to different location altogether
			if path.startswith('/assets/'):
				path = path.replace('/assets/', 'assets/')
			try:
				with open(os.path.join(dataent.local.sites_path, path) ,"r") as f:
					assets[0]["data"] = assets[0]["data"] + "\n" + dataent.safe_decode(f.read(), "utf-8")
			except IOError:
				pass

		for path in data["include_css"]:
			if path.startswith('/assets/'):
				path = path.replace('/assets/', 'assets/')
			try:
				with open(os.path.join(dataent.local.sites_path, path) ,"r") as f:
					assets[1]["data"] = assets[1]["data"] + "\n" + dataent.safe_decode(f.read(), "utf-8")
			except IOError:
				pass

	return {
		"build_version": data["build_version"],
		"boot": data["boot"],
		"assets": assets
	}

def get_build_version():
	try:
		return str(os.path.getmtime(os.path.join(dataent.local.sites_path, '.build')))
	except OSError:
		# .build can sometimes not exist
		# this is not a major problem so send fallback
		return dataent.utils.random_string(8)
