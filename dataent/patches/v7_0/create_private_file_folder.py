from __future__ import unicode_literals
import dataent, os

def execute():
	if not os.path.exists(os.path.join(dataent.local.site_path, 'private', 'files')):
		dataent.create_folder(os.path.join(dataent.local.site_path, 'private', 'files'))