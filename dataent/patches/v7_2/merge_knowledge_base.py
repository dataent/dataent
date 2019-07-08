from __future__ import unicode_literals
import dataent

from dataent.patches.v7_0.re_route import update_routes
from dataent.installer import remove_from_installed_apps

def execute():
	if 'knowledge_base' in dataent.get_installed_apps():
		dataent.reload_doc('website', 'doctype', 'help_category')
		dataent.reload_doc('website', 'doctype', 'help_article')
		update_routes(['Help Category', 'Help Article'])
		remove_from_installed_apps('knowledge_base')

		# remove desktop icon
		desktop_icon_name = dataent.db.get_value('Desktop Icon',
			dict(module_name='Knowledge Base', type='module'))
		if desktop_icon_name:
			dataent.delete_doc('Desktop Icon', desktop_icon_name)

		# remove module def
		if dataent.db.exists('Module Def', 'Knowledge Base'):
			dataent.delete_doc('Module Def', 'Knowledge Base')

		# set missing routes
		for doctype in ('Help Category', 'Help Article'):
			for d in dataent.get_all(doctype, fields=['name', 'route']):
				if not d.route:
					doc = dataent.get_doc(doctype, d.name)
					doc.set_route()
					doc.db_update()