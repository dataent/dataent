# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import os
from six import iteritems
import logging

from werkzeug.wrappers import Request
from werkzeug.local import LocalManager
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.contrib.profiler import ProfilerMiddleware
from werkzeug.wsgi import SharedDataMiddleware

import dataent
import dataent.handler
import dataent.auth
import dataent.api
import dataent.utils.response
import dataent.website.render
from dataent.utils import get_site_name
from dataent.middlewares import StaticDataMiddleware
from dataent.utils.error import make_error_snapshot
from dataent.core.doctype.communication.comment import update_comments_in_parent_after_request
from dataent import _

# imports - third-party imports
import pymysql
from pymysql.constants import ER

# imports - module imports

local_manager = LocalManager([dataent.local])

_site = None
_sites_path = os.environ.get("SITES_PATH", ".")

class RequestContext(object):

	def __init__(self, environ):
		self.request = Request(environ)

	def __enter__(self):
		init_request(self.request)

	def __exit__(self, type, value, traceback):
		dataent.destroy()


@Request.application
def application(request):
	response = None

	try:
		rollback = True

		init_request(request)

		if dataent.local.form_dict.cmd:
			response = dataent.handler.handle()

		elif dataent.request.path.startswith("/api/"):
			if dataent.local.form_dict.data is None:
					dataent.local.form_dict.data = request.get_data()
			response = dataent.api.handle()

		elif dataent.request.path.startswith('/backups'):
			response = dataent.utils.response.download_backup(request.path)

		elif dataent.request.path.startswith('/private/files/'):
			response = dataent.utils.response.download_private_file(request.path)

		elif dataent.local.request.method in ('GET', 'HEAD', 'POST'):
			response = dataent.website.render.render()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except dataent.SessionStopped as e:
		response = dataent.utils.response.handle_session_stopped()

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = after_request(rollback)

	finally:
		if dataent.local.request.method in ("POST", "PUT") and dataent.db and rollback:
			dataent.db.rollback()

		# set cookies
		if response and hasattr(dataent.local, 'cookie_manager'):
			dataent.local.cookie_manager.flush_cookies(response=response)

		dataent.destroy()

	return response

def init_request(request):
	dataent.local.request = request
	dataent.local.is_ajax = dataent.get_request_header("X-Requested-With")=="XMLHttpRequest"

	site = _site or request.headers.get('X-Dataent-Site-Name') or get_site_name(request.host)
	dataent.init(site=site, sites_path=_sites_path)

	if not (dataent.local.conf and dataent.local.conf.db_name):
		# site does not exist
		raise NotFound

	if dataent.local.conf.get('maintenance_mode'):
		raise dataent.SessionStopped

	make_form_dict(request)

	dataent.local.http_request = dataent.auth.HTTPRequest()

def make_form_dict(request):
	import json

	if 'application/json' in (request.content_type or '') and request.data:
		args = json.loads(request.data)
	else:
		args = request.form or request.args

	try:
		dataent.local.form_dict = dataent._dict({ k:v[0] if isinstance(v, (list, tuple)) else v \
			for k, v in iteritems(args) })
	except IndexError:
		dataent.local.form_dict = dataent._dict(args)

	if "_" in dataent.local.form_dict:
		# _ is passed by $.ajax so that the request is not cached by the browser. So, remove _ from form_dict
		dataent.local.form_dict.pop("_")

def handle_exception(e):
	response = None
	http_status_code = getattr(e, "http_status_code", 500)
	return_as_message = False

	if dataent.get_request_header('Accept') and (dataent.local.is_ajax or 'application/json' in dataent.get_request_header('Accept')):
		# handle ajax responses first
		# if the request is ajax, send back the trace or error message
		response = dataent.utils.response.report_error(http_status_code)

	elif (http_status_code==500
		and isinstance(e, pymysql.InternalError)
		and e.args[0] in (ER.LOCK_WAIT_TIMEOUT, ER.LOCK_DEADLOCK)):
			http_status_code = 508

	elif http_status_code==401:
		dataent.respond_as_web_page(_("Session Expired"),
			_("Your session has expired, please login again to continue."),
			http_status_code=http_status_code,  indicator_color='red')
		return_as_message = True

	elif http_status_code==403:
		dataent.respond_as_web_page(_("Not Permitted"),
			_("You do not have enough permissions to complete the action"),
			http_status_code=http_status_code,  indicator_color='red')
		return_as_message = True

	elif http_status_code==404:
		dataent.respond_as_web_page(_("Not Found"),
			_("The resource you are looking for is not available"),
			http_status_code=http_status_code,  indicator_color='red')
		return_as_message = True

	else:
		traceback = "<pre>"+dataent.get_traceback()+"</pre>"
		if dataent.local.flags.disable_traceback:
			traceback = ""

		dataent.respond_as_web_page("Server Error",
			traceback, http_status_code=http_status_code,
			indicator_color='red', width=640)
		return_as_message = True

	if e.__class__ == dataent.AuthenticationError:
		if hasattr(dataent.local, "login_manager"):
			dataent.local.login_manager.clear_cookies()

	if http_status_code >= 500:
		dataent.logger().error('Request Error', exc_info=True)
		make_error_snapshot(e)

	if return_as_message:
		response = dataent.website.render.render("message",
			http_status_code=http_status_code)

	return response

def after_request(rollback):
	if (dataent.local.request.method in ("POST", "PUT") or dataent.local.flags.commit) and dataent.db:
		if dataent.db.transaction_writes:
			dataent.db.commit()
			rollback = False

	# update session
	if getattr(dataent.local, "session_obj", None):
		updated_in_db = dataent.local.session_obj.update()
		if updated_in_db:
			dataent.db.commit()
			rollback = False

	update_comments_in_parent_after_request()

	return rollback

application = local_manager.make_middleware(application)

def serve(port=8000, profile=False, no_reload=False, no_threading=False, site=None, sites_path='.'):
	global application, _site, _sites_path
	_site = site
	_sites_path = sites_path

	from werkzeug.serving import run_simple

	if profile:
		application = ProfilerMiddleware(application, sort_by=('cumtime', 'calls'))

	if not os.environ.get('NO_STATICS'):
		application = SharedDataMiddleware(application, {
			'/assets': os.path.join(sites_path, 'assets'),
		})

		application = StaticDataMiddleware(application, {
			'/files': os.path.abspath(sites_path)
		})

	application.debug = True
	application.config = {
		'SERVER_NAME': 'localhost:8000'
	}

	in_test_env = os.environ.get('CI')
	if in_test_env:
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)

	run_simple('0.0.0.0', int(port), application,
		use_reloader=False if in_test_env else not no_reload,
		use_debugger=not in_test_env,
		use_evalex=not in_test_env,
		threaded=not no_threading)
