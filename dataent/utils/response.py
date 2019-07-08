# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import json
import datetime
import decimal
import mimetypes
import os
import dataent
from dataent import _
import dataent.model.document
import dataent.utils
import dataent.sessions
import werkzeug.utils
from werkzeug.local import LocalProxy
from werkzeug.wsgi import wrap_file
from werkzeug.wrappers import Response
from werkzeug.exceptions import NotFound, Forbidden
from dataent.core.doctype.file.file import check_file_permission
from dataent.website.render import render
from dataent.utils import cint
from six import text_type
from six.moves.urllib.parse import quote

def report_error(status_code):
	'''Build error. Show traceback in developer mode'''
	if (cint(dataent.db.get_system_setting('allow_error_traceback'))
		and (status_code!=404 or dataent.conf.logging)
		and not dataent.local.flags.disable_traceback):
		dataent.errprint(dataent.utils.get_traceback())

	response = build_response("json")
	response.status_code = status_code
	return response

def build_response(response_type=None):
	if "docs" in dataent.local.response and not dataent.local.response.docs:
		del dataent.local.response["docs"]

	response_type_map = {
		'csv': as_csv,
		'txt': as_txt,
		'download': as_raw,
		'json': as_json,
		'pdf': as_pdf,
		'page': as_page,
		'redirect': redirect,
		'binary': as_binary
	}

	return response_type_map[dataent.response.get('type') or response_type]()

def as_csv():
	response = Response()
	response.mimetype = 'text/csv'
	response.charset = 'utf-8'
	response.headers["Content-Disposition"] = ("attachment; filename=\"%s.csv\"" % dataent.response['doctype'].replace(' ', '_')).encode("utf-8")
	response.data = dataent.response['result']
	return response

def as_txt():
	response = Response()
	response.mimetype = 'text'
	response.charset = 'utf-8'
	response.headers["Content-Disposition"] = ("attachment; filename=\"%s.txt\"" % dataent.response['doctype'].replace(' ', '_')).encode("utf-8")
	response.data = dataent.response['result']
	return response

def as_raw():
	response = Response()
	response.mimetype = dataent.response.get("content_type") or mimetypes.guess_type(dataent.response['filename'])[0] or "application/unknown"
	response.headers["Content-Disposition"] = ("attachment; filename=\"%s\"" % dataent.response['filename'].replace(' ', '_')).encode("utf-8")
	response.data = dataent.response['filecontent']
	return response

def as_json():
	make_logs()
	response = Response()
	if dataent.local.response.http_status_code:
		response.status_code = dataent.local.response['http_status_code']
		del dataent.local.response['http_status_code']

	response.mimetype = 'application/json'
	response.charset = 'utf-8'
	response.data = json.dumps(dataent.local.response, default=json_handler, separators=(',',':'))
	return response

def as_pdf():
	response = Response()
	response.mimetype = "application/pdf"
	response.headers["Content-Disposition"] = ("filename=\"%s\"" % dataent.response['filename'].replace(' ', '_')).encode("utf-8")
	response.data = dataent.response['filecontent']
	return response

def as_binary():
	response = Response()
	response.mimetype = 'application/octet-stream'
	response.headers["Content-Disposition"] = ("filename=\"%s\"" % dataent.response['filename'].replace(' ', '_')).encode("utf-8")
	response.data = dataent.response['filecontent']
	return response

def make_logs(response = None):
	"""make strings for msgprint and errprint"""
	if not response:
		response = dataent.local.response

	if dataent.error_log:
		response['exc'] = json.dumps([dataent.utils.cstr(d["exc"]) for d in dataent.local.error_log])

	if dataent.local.message_log:
		response['_server_messages'] = json.dumps([dataent.utils.cstr(d) for
			d in dataent.local.message_log])

	if dataent.debug_log and dataent.conf.get("logging") or False:
		response['_debug_messages'] = json.dumps(dataent.local.debug_log)

	if dataent.flags.error_message:
		response['_error_message'] = dataent.flags.error_message

def json_handler(obj):
	"""serialize non-serializable data for json"""
	# serialize date
	import collections

	if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
		return text_type(obj)

	elif isinstance(obj, decimal.Decimal):
		return float(obj)

	elif isinstance(obj, LocalProxy):
		return text_type(obj)

	elif isinstance(obj, dataent.model.document.BaseDocument):
		doc = obj.as_dict(no_nulls=True)
		return doc

	elif isinstance(obj, collections.Iterable):
		return list(obj)

	elif type(obj)==type or isinstance(obj, Exception):
		return repr(obj)

	else:
		raise TypeError("""Object of type %s with value of %s is not JSON serializable""" % \
						(type(obj), repr(obj)))

def as_page():
	"""print web page"""
	return render(dataent.response['route'], http_status_code=dataent.response.get("http_status_code"))

def redirect():
	return werkzeug.utils.redirect(dataent.response.location)

def download_backup(path):
	try:
		dataent.only_for(("System Manager", "Administrator"))
	except dataent.PermissionError:
		raise Forbidden(_("You need to be logged in and have System Manager Role to be able to access backups."))

	return send_private_file(path)

def download_private_file(path):
	"""Checks permissions and sends back private file"""
	try:
		check_file_permission(path)

	except dataent.PermissionError:
		raise Forbidden(_("You don't have permission to access this file"))

	return send_private_file(path.split("/private", 1)[1])


def send_private_file(path):
	path = os.path.join(dataent.local.conf.get('private_path', 'private'), path.strip("/"))
	filename = os.path.basename(path)

	if dataent.local.request.headers.get('X-Use-X-Accel-Redirect'):
		path = '/protected/' + path
		response = Response()
		response.headers['X-Accel-Redirect'] = quote(dataent.utils.encode(path))

	else:
		filepath = dataent.utils.get_site_path(path)
		try:
			f = open(filepath, 'rb')
		except IOError:
			raise NotFound

		response = Response(wrap_file(dataent.local.request.environ, f), direct_passthrough=True)

	# no need for content disposition and force download. let browser handle its opening.
	# response.headers.add(b'Content-Disposition', b'attachment', filename=filename.encode("utf-8"))

	response.mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

	return response

def handle_session_stopped():
	dataent.respond_as_web_page(_("Updating"),
		_("Your system is being updated. Please refresh again after a few moments"),
		http_status_code=503, indicator_color='orange', fullpage = True, primary_action=None)
	return dataent.website.render.render("message", http_status_code=503)
