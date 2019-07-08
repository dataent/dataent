# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent, os
from dataent import _
import dataent.modules.import_file
from dataent.model.document import Document
from dataent.utils.data import format_datetime
from dataent.core.doctype.data_import.importer import upload
from dataent.utils.background_jobs import enqueue


class DataImport(Document):
	def autoname(self):
		if not self.name:
			self.name = "Import on "+ format_datetime(self.creation)

	def validate(self):
		if not self.import_file:
			self.db_set("total_rows", 0)
		if self.import_status == "In Progress":
			dataent.throw(_("Can't save the form as data import is in progress."))

		# validate the template just after the upload
		# if there is total_rows in the doc, it means that the template is already validated and error free
		if self.import_file and not self.total_rows:
			upload(data_import_doc=self, from_data_import="Yes", validate_template=True)


@dataent.whitelist()
def import_data(data_import):
	dataent.db.set_value("Data Import", data_import, "import_status", "In Progress", update_modified=False)
	dataent.publish_realtime("data_import_progress", {"progress": "0",
		"data_import": data_import, "reload": True}, user=dataent.session.user)

	from dataent.core.page.background_jobs.background_jobs import get_info
	enqueued_jobs = [d.get("job_name") for d in get_info()]

	if data_import not in enqueued_jobs:
		enqueue(upload, queue='default', timeout=6000, event='data_import', job_name=data_import,
			data_import_doc=data_import, from_data_import="Yes", user=dataent.session.user)


def import_doc(path, overwrite=False, ignore_links=False, ignore_insert=False,
	insert=False, submit=False, pre_process=None):
	if os.path.isdir(path):
		files = [os.path.join(path, f) for f in os.listdir(path)]
	else:
		files = [path]

	for f in files:
		if f.endswith(".json"):
			dataent.flags.mute_emails = True
			dataent.modules.import_file.import_file_by_path(f, data_import=True, force=True, pre_process=pre_process, reset_permissions=True)
			dataent.flags.mute_emails = False
			dataent.db.commit()
		elif f.endswith(".csv"):
			import_file_by_path(f, ignore_links=ignore_links, overwrite=overwrite, submit=submit, pre_process=pre_process)
			dataent.db.commit()


def import_file_by_path(path, ignore_links=False, overwrite=False, submit=False, pre_process=None, no_email=True):
	from dataent.utils.csvutils import read_csv_content
	print("Importing " + path)
	with open(path, "r") as infile:
		upload(rows = read_csv_content(infile.read()), ignore_links=ignore_links, no_email=no_email, overwrite=overwrite,
			submit_after_import=submit, pre_process=pre_process)


def export_json(doctype, path, filters=None, or_filters=None, name=None, order_by="creation asc"):
	def post_process(out):
		del_keys = ('modified_by', 'creation', 'owner', 'idx')
		for doc in out:
			for key in del_keys:
				if key in doc:
					del doc[key]
			for k, v in doc.items():
				if isinstance(v, list):
					for child in v:
						for key in del_keys + ('docstatus', 'doctype', 'modified', 'name'):
							if key in child:
								del child[key]

	out = []
	if name:
		out.append(dataent.get_doc(doctype, name).as_dict())
	elif dataent.db.get_value("DocType", doctype, "issingle"):
		out.append(dataent.get_doc(doctype).as_dict())
	else:
		for doc in dataent.get_all(doctype, fields=["name"], filters=filters, or_filters=or_filters, limit_page_length=0, order_by=order_by):
			out.append(dataent.get_doc(doctype, doc.name).as_dict())
	post_process(out)

	dirname = os.path.dirname(path)
	if not os.path.exists(dirname):
		path = os.path.join('..', path)

	with open(path, "w") as outfile:
		outfile.write(dataent.as_json(out))


def export_csv(doctype, path):
	from dataent.core.doctype.data_export.exporter import export_data
	with open(path, "wb") as csvfile:
		export_data(doctype=doctype, all_doctypes=True, template=True, with_data=True)
		csvfile.write(dataent.response.result.encode("utf-8"))


@dataent.whitelist()
def export_fixture(doctype, app):
	if dataent.session.user != "Administrator":
		raise dataent.PermissionError

	if not os.path.exists(dataent.get_app_path(app, "fixtures")):
		os.mkdir(dataent.get_app_path(app, "fixtures"))

	export_json(doctype, dataent.get_app_path(app, "fixtures", dataent.scrub(doctype) + ".json"), order_by="name asc")
