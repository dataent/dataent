from __future__ import unicode_literals
import dataent
from dataent.model.rename_doc import rename_doc


def execute():
	if dataent.db.table_exists("Workflow Action") and not dataent.db.table_exists("Workflow Action Master"):
		rename_doc('DocType', 'Workflow Action', 'Workflow Action Master')
		dataent.reload_doc('workflow', 'doctype', 'workflow_action_master')
