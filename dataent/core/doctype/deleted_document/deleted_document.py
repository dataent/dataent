# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent, json
from dataent.model.document import Document
from dataent import _

class DeletedDocument(Document):
	pass

@dataent.whitelist()
def restore(name):
	deleted = dataent.get_doc('Deleted Document', name)
	doc = dataent.get_doc(json.loads(deleted.data))
	try:
		doc.insert()
	except dataent.DocstatusTransitionError:
		dataent.msgprint(_("Cancelled Document restored as Draft"))
		doc.docstatus = 0
		doc.insert()

	doc.add_comment('Edit', _('restored {0} as {1}').format(deleted.deleted_name, doc.name))

	deleted.new_name = doc.name
	deleted.restored = 1
	deleted.db_update()

	dataent.msgprint(_('Document Restored'))
