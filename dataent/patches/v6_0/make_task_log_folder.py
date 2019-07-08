from __future__ import unicode_literals
import dataent.utils, os

def execute():
	path = dataent.utils.get_site_path('task-logs')
	if not os.path.exists(path):
		os.makedirs(path)
