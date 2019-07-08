from __future__ import unicode_literals
import dataent

from dataent.core.doctype.communication.comment import update_comment_in_doc

def execute():
	for d in dataent.db.get_all("Communication",
		fields = ['name', 'reference_doctype', 'reference_name', 'SUBSTRING(content,1,102)', 'communication_type'],
		filters = {"reference_name":None,"reference_doctype":None,'communication_type': 'Communication'}):

		try:
			update_comment_in_doc(d)
		except dataent.ImplicitCommitError:
			pass
