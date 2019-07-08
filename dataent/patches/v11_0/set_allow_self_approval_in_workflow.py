from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("workflow", "doctype", "workflow_transition")
	dataent.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")