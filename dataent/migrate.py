# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import json
import os
import dataent
import dataent.translate
import dataent.modules.patch_handler
import dataent.model.sync
from dataent.utils.fixtures import sync_fixtures
from dataent.cache_manager import clear_global_cache
from dataent.desk.notifications import clear_notifications
from dataent.website import render, router
from dataent.desk.doctype.desktop_icon.desktop_icon import sync_desktop_icons
from dataent.core.doctype.language.language import sync_languages
from dataent.modules.utils import sync_customizations

def migrate(verbose=True, rebuild_website=False):
	'''Migrate all apps to the latest version, will:
	- run before migrate hooks
	- run patches
	- sync doctypes (schema)
	- sync fixtures
	- sync desktop icons
	- sync web pages (from /www)
	- sync web pages (from /www)
	- run after migrate hooks
	'''

	touched_tables_file = dataent.get_site_path('touched_tables.json')
	if os.path.exists(touched_tables_file):
		os.remove(touched_tables_file)

	try:
		dataent.flags.touched_tables = set()
		dataent.flags.in_migrate = True
		clear_global_cache()

		#run before_migrate hooks
		for app in dataent.get_installed_apps():
			for fn in dataent.get_hooks('before_migrate', app_name=app):
				dataent.get_attr(fn)()

		# run patches
		dataent.modules.patch_handler.run_all()
		# sync
		dataent.model.sync.sync_all(verbose=verbose)
		dataent.translate.clear_cache()
		sync_fixtures()
		sync_customizations()
		sync_desktop_icons()
		sync_languages()

		dataent.get_doc('Portal Settings', 'Portal Settings').sync_menu()

		# syncs statics
		render.clear_cache()

		# add static pages to global search
		router.sync_global_search()

		#run after_migrate hooks
		for app in dataent.get_installed_apps():
			for fn in dataent.get_hooks('after_migrate', app_name=app):
				dataent.get_attr(fn)()

		dataent.db.commit()

		clear_notifications()

		dataent.publish_realtime("version-update")
		dataent.flags.in_migrate = False
	finally:
		with open(touched_tables_file, 'w') as f:
			json.dump(list(dataent.flags.touched_tables), f, sort_keys=True, indent=4)
		dataent.flags.touched_tables.clear()

