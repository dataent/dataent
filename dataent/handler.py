# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
import dataent.utils
import dataent.sessions
import dataent.utils.file_manager
import dataent.desk.form.run_method
from dataent.utils.response import build_response
from werkzeug.wrappers import Response
from six import string_types

def handle():
	"""handle request"""
	cmd = dataent.local.form_dict.cmd
	data = None

	if cmd!='login':
		data = execute_cmd(cmd)

	# data can be an empty string or list which are valid responses
	if data is not None:
		if isinstance(data, Response):
			# method returns a response object, pass it on
			return data

		# add the response to `message` label
		dataent.response['message'] = data

	return build_response("json")

def execute_cmd(cmd, from_async=False):
	"""execute a request as python module"""
	for hook in dataent.get_hooks("override_whitelisted_methods", {}).get(cmd, []):
		# override using the first hook
		cmd = hook
		break

	try:
		method = get_attr(cmd)
	except Exception as e:
		if dataent.local.conf.developer_mode:
			raise e
		else:
			dataent.respond_as_web_page(title='Invalid Method', html='Method not found',
			indicator_color='red', http_status_code=404)
		return

	if from_async:
		method = method.queue

	is_whitelisted(method)

	return dataent.call(method, **dataent.form_dict)


def is_whitelisted(method):
	# check if whitelisted
	if dataent.session['user'] == 'Guest':
		if (method not in dataent.guest_methods):
			dataent.msgprint(_("Not permitted"))
			raise dataent.PermissionError('Not Allowed, {0}'.format(method))

		if method not in dataent.xss_safe_methods:
			# strictly sanitize form_dict
			# escapes html characters like <> except for predefined tags like a, b, ul etc.
			for key, value in dataent.form_dict.items():
				if isinstance(value, string_types):
					dataent.form_dict[key] = dataent.utils.sanitize_html(value)

	else:
		if not method in dataent.whitelisted:
			dataent.msgprint(_("Not permitted"))
			raise dataent.PermissionError('Not Allowed, {0}'.format(method))

@dataent.whitelist(allow_guest=True)
def version():
	return dataent.__version__

@dataent.whitelist()
def runserverobj(method, docs=None, dt=None, dn=None, arg=None, args=None):
	dataent.desk.form.run_method.runserverobj(method, docs=docs, dt=dt, dn=dn, arg=arg, args=args)

@dataent.whitelist(allow_guest=True)
def logout():
	dataent.local.login_manager.logout()
	dataent.db.commit()

@dataent.whitelist(allow_guest=True)
def web_logout():
	dataent.local.login_manager.logout()
	dataent.db.commit()
	dataent.respond_as_web_page(_("Logged Out"), _("You have been successfully logged out"),
		indicator_color='green')

@dataent.whitelist(allow_guest=True)
def run_custom_method(doctype, name, custom_method):
	"""cmd=run_custom_method&doctype={doctype}&name={name}&custom_method={custom_method}"""
	doc = dataent.get_doc(doctype, name)
	if getattr(doc, custom_method, dataent._dict()).is_whitelisted:
		dataent.call(getattr(doc, custom_method), **dataent.local.form_dict)
	else:
		dataent.throw(_("Not permitted"), dataent.PermissionError)

@dataent.whitelist()
def uploadfile():
	ret = None

	try:
		if dataent.form_dict.get('from_form'):
			try:
				ret = dataent.utils.file_manager.upload()
			except dataent.DuplicateEntryError:
				# ignore pass
				ret = None
				dataent.db.rollback()
		else:
			if dataent.form_dict.get('method'):
				method = dataent.get_attr(dataent.form_dict.method)
				is_whitelisted(method)
				ret = method()
	except Exception:
		dataent.errprint(dataent.utils.get_traceback())
		dataent.response['http_status_code'] = 500
		ret = None

	return ret


def get_attr(cmd):
	"""get method object from cmd"""
	if '.' in cmd:
		method = dataent.get_attr(cmd)
	else:
		method = globals()[cmd]
	dataent.log("method:" + cmd)
	return method

@dataent.whitelist(allow_guest = True)
def ping():
	return "pong"
