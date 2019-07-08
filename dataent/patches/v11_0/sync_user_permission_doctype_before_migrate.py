from __future__ import unicode_literals
import dataent

def execute():
	dataent.flags.in_patch = True
	dataent.reload_doc('core', 'doctype', 'user_permission')
	dataent.db.commit()
