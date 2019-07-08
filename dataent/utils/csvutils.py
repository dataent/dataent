# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent import msgprint, _
import json
import csv
import six
from six import StringIO, text_type, string_types
from dataent.utils import encode, cstr, cint, flt, comma_or

def read_csv_content_from_uploaded_file(ignore_encoding=False):
	if getattr(dataent, "uploaded_file", None):
		with open(dataent.uploaded_file, "r") as upfile:
			fcontent = upfile.read()
	else:
		from dataent.utils.file_manager import get_uploaded_content
		fname, fcontent = get_uploaded_content()
	return read_csv_content(fcontent, ignore_encoding)

def read_csv_content_from_attached_file(doc):
	fileid = dataent.get_all("File", fields = ["name"], filters = {"attached_to_doctype": doc.doctype,
		"attached_to_name":doc.name}, order_by="creation desc")

	if fileid : fileid = fileid[0].name

	if not fileid:
		msgprint(_("File not attached"))
		raise Exception

	try:
		from dataent.utils.file_manager import get_file
		fname, fcontent = get_file(fileid)
		return read_csv_content(fcontent, dataent.form_dict.get('ignore_encoding_errors'))
	except Exception:
		dataent.throw(_("Unable to open attached file. Did you export it as CSV?"), title=_('Invalid CSV Format'))

def read_csv_content(fcontent, ignore_encoding=False):
	rows = []

	if not isinstance(fcontent, text_type):
		decoded = False
		for encoding in ["utf-8", "windows-1250", "windows-1252"]:
			try:
				fcontent = text_type(fcontent, encoding)
				decoded = True
				break
			except UnicodeDecodeError:
				continue

		if not decoded:
			dataent.msgprint(_("Unknown file encoding. Tried utf-8, windows-1250, windows-1252."), raise_exception=True)

	fcontent = fcontent.encode("utf-8")
	content  = [ ]
	for line in fcontent.splitlines(True):
		if six.PY2:
			content.append(line)
		else:
			content.append(dataent.safe_decode(line))

	try:
		rows = []
		for row in csv.reader(content):
			r = []
			for val in row:
				# decode everything
				val = val.strip()

				if val=="":
					# reason: in maraidb strict config, one cannot have blank strings for non string datatypes
					r.append(None)
				else:
					r.append(val)

			rows.append(r)

		return rows

	except Exception:
		dataent.msgprint(_("Not a valid Comma Separated Value (CSV File)"))
		raise

@dataent.whitelist()
def send_csv_to_client(args):
	if isinstance(args, string_types):
		args = json.loads(args)

	args = dataent._dict(args)

	dataent.response["result"] = cstr(to_csv(args.data))
	dataent.response["doctype"] = args.filename
	dataent.response["type"] = "csv"

def to_csv(data):
	writer = UnicodeWriter()
	for row in data:
		writer.writerow(row)

	return writer.getvalue()


class UnicodeWriter:
	def __init__(self, encoding="utf-8"):
		self.encoding = encoding
		self.queue = StringIO()
		self.writer = csv.writer(self.queue, quoting=csv.QUOTE_NONNUMERIC)

	def writerow(self, row):
		if six.PY2:
			row = encode(row, self.encoding)
		self.writer.writerow(row)

	def getvalue(self):
		return self.queue.getvalue()

def check_record(d):
	"""check for mandatory, select options, dates. these should ideally be in doclist"""
	from dataent.utils.dateutils import parse_date
	doc = dataent.get_doc(d)

	for key in d:
		docfield = doc.meta.get_field(key)
		val = d[key]
		if docfield:
			if docfield.reqd and (val=='' or val==None):
				dataent.msgprint(_("{0} is required").format(docfield.label), raise_exception=1)

			if docfield.fieldtype=='Select' and val and docfield.options:
				if val not in docfield.options.split('\n'):
					dataent.throw(_("{0} must be one of {1}").format(_(docfield.label), comma_or(docfield.options.split("\n"))))

			if val and docfield.fieldtype=='Date':
				d[key] = parse_date(val)
			elif val and docfield.fieldtype in ["Int", "Check"]:
				d[key] = cint(val)
			elif val and docfield.fieldtype in ["Currency", "Float", "Percent"]:
				d[key] = flt(val)

def import_doc(d, doctype, overwrite, row_idx, submit=False, ignore_links=False):
	"""import main (non child) document"""
	if d.get("name") and dataent.db.exists(doctype, d['name']):
		if overwrite:
			doc = dataent.get_doc(doctype, d['name'])
			doc.flags.ignore_links = ignore_links
			doc.update(d)
			if d.get("docstatus") == 1:
				doc.update_after_submit()
			elif d.get("docstatus") == 0 and submit:
				doc.submit()
			else:
				doc.save()
			return 'Updated row (#%d) %s' % (row_idx + 1, getlink(doctype, d['name']))
		else:
			return 'Ignored row (#%d) %s (exists)' % (row_idx + 1,
				getlink(doctype, d['name']))
	else:
		doc = dataent.get_doc(d)
		doc.flags.ignore_links = ignore_links
		doc.insert()

		if submit:
			doc.submit()

		return 'Inserted row (#%d) %s' % (row_idx + 1, getlink(doctype,
			doc.get('name')))

def getlink(doctype, name):
	return '<a href="#Form/%(doctype)s/%(name)s">%(name)s</a>' % locals()
