from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype('System Settings')
	doc = dataent.get_single('System Settings')
	doc.enable_chat = 1

	# Changes prescribed by Nabin Hait (nabin@epaas.xyz)
	doc.flags.ignore_mandatory   = True
	doc.flags.ignore_permissions = True

	doc.save()