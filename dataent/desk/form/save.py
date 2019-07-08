# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent, json
from dataent.desk.form.load import run_onload

@dataent.whitelist()
def savedocs(doc, action):
	"""save / submit / update doclist"""
	try:
		doc = dataent.get_doc(json.loads(doc))
		set_local_name(doc)

		# action
		doc.docstatus = {"Save":0, "Submit": 1, "Update": 1, "Cancel": 2}[action]

		if doc.docstatus==1:
			doc.submit()
		else:
			try:
				doc.save()
			except dataent.NameError as e:
				doctype, name, original_exception = e if isinstance(e, tuple) else (doc.doctype or "", doc.name or "", None)
				dataent.msgprint(dataent._("{0} {1} already exists").format(doctype, name))
				raise

		# update recent documents
		run_onload(doc)
		dataent.get_user().update_recent(doc.doctype, doc.name)
		send_updated_docs(doc)
	except Exception:
		dataent.errprint(dataent.utils.get_traceback())
		raise

@dataent.whitelist()
def cancel(doctype=None, name=None, workflow_state_fieldname=None, workflow_state=None):
	"""cancel a doclist"""
	try:
		doc = dataent.get_doc(doctype, name)
		if workflow_state_fieldname and workflow_state:
			doc.set(workflow_state_fieldname, workflow_state)
		doc.cancel()
		send_updated_docs(doc)

	except Exception:
		dataent.errprint(dataent.utils.get_traceback())
		dataent.msgprint(dataent._("Did not cancel"))
		raise

def send_updated_docs(doc):
	from .load import get_docinfo
	get_docinfo(doc)

	d = doc.as_dict()
	if hasattr(doc, 'localname'):
		d["localname"] = doc.localname

	dataent.response.docs.append(d)

def set_local_name(doc):
	def _set_local_name(d):
		if doc.get('__islocal') or d.get('__islocal'):
			d.localname = d.name
			d.name = None

	_set_local_name(doc)
	for child in doc.get_all_children():
		_set_local_name(child)

	if doc.get("__newname"):
		doc.name = doc.get("__newname")
