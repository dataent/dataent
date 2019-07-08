# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

def get_jenv():
	import dataent

	if not getattr(dataent.local, 'jenv', None):
		from jinja2 import Environment, DebugUndefined

		# dataent will be loaded last, so app templates will get precedence
		jenv = Environment(loader = get_jloader(),
			undefined=DebugUndefined)
		set_filters(jenv)

		jenv.globals.update(get_allowed_functions_for_jenv())

		dataent.local.jenv = jenv

	return dataent.local.jenv

def get_template(path):
	return get_jenv().get_template(path)

def get_email_from_template(name, args):
	from jinja2 import TemplateNotFound

	args = args or {}
	try:
		message = get_template('templates/emails/' + name + '.html').render(args)
	except TemplateNotFound as e:
		raise e

	try:
		text_content = get_template('templates/emails/' + name + '.txt').render(args)
	except TemplateNotFound:
		text_content = None

	return (message, text_content)

def validate_template(html):
	"""Throws exception if there is a syntax error in the Jinja Template"""
	import dataent
	from jinja2 import TemplateSyntaxError

	jenv = get_jenv()
	try:
		jenv.from_string(html)
	except TemplateSyntaxError as e:
		dataent.msgprint('Line {}: {}'.format(e.lineno, e.message))
		dataent.throw(dataent._("Syntax error in template"))

def render_template(template, context, is_path=None, safe_render=True):
	'''Render a template using Jinja

	:param template: path or HTML containing the jinja template
	:param context: dict of properties to pass to the template
	:param is_path: (optional) assert that the `template` parameter is a path
	:param safe_render: (optional) prevent server side scripting via jinja templating
	'''

	from dataent import get_traceback, throw
	from jinja2 import TemplateError

	if not template:
		return ""

	# if it ends with .html then its a freaking path, not html
	if (is_path
		or template.startswith("templates/")
		or (template.endswith('.html') and '\n' not in template)):
		return get_jenv().get_template(template).render(context)
	else:
		if safe_render and ".__" in template:
			throw("Illegal template")
		try:
			return get_jenv().from_string(template).render(context)
		except TemplateError:
			throw(title="Jinja Template Error", msg="<pre>{template}</pre><pre>{tb}</pre>".format(template=template, tb=get_traceback()))


def get_allowed_functions_for_jenv():
	import os, json
	import dataent
	import dataent.utils
	import dataent.utils.data
	from dataent.utils.autodoc import automodule, get_version
	from dataent.model.document import get_controller
	from dataent.website.utils import (get_shade, get_toc, get_next_link)
	from dataent.modules import scrub
	import mimetypes
	from html2text import html2text
	from dataent.www.printview import get_visible_columns

	datautils = {}
	if dataent.db:
		date_format = dataent.db.get_default("date_format") or "yyyy-mm-dd"
	else:
		date_format = 'yyyy-mm-dd'

	for key, obj in dataent.utils.data.__dict__.items():
		if key.startswith("_"):
			# ignore
			continue

		if hasattr(obj, "__call__"):
			# only allow functions
			datautils[key] = obj

	if "_" in getattr(dataent.local, 'form_dict', {}):
		del dataent.local.form_dict["_"]

	user = getattr(dataent.local, "session", None) and dataent.local.session.user or "Guest"

	out = {
		# make available limited methods of dataent
		"dataent": {
			"_": dataent._,
			"get_url": dataent.utils.get_url,
			'format': dataent.format_value,
			"format_value": dataent.format_value,
			'date_format': date_format,
			"format_date": dataent.utils.data.global_date_format,
			"form_dict": getattr(dataent.local, 'form_dict', {}),
			"get_hooks": dataent.get_hooks,
			"get_meta": dataent.get_meta,
			"get_doc": dataent.get_doc,
			"get_list": dataent.get_list,
			"get_all": dataent.get_all,
			'get_system_settings': dataent.get_system_settings,
			"utils": datautils,
			"user": user,
			"get_fullname": dataent.utils.get_fullname,
			"get_gravatar": dataent.utils.get_gravatar_url,
			"full_name": dataent.local.session.data.full_name if getattr(dataent.local, "session", None) else "Guest",
			"render_template": dataent.render_template,
			"request": getattr(dataent.local, 'request', {}),
			'session': {
				'user': user,
				'csrf_token': dataent.local.session.data.csrf_token if getattr(dataent.local, "session", None) else ''
			},
			"socketio_port": dataent.conf.socketio_port,
		},
		'style': {
			'border_color': '#d1d8dd'
		},
		"autodoc": {
			"get_version": get_version,
			"automodule": automodule,
			"get_controller": get_controller
		},
		'get_toc': get_toc,
		'get_next_link': get_next_link,
		"_": dataent._,
		"get_shade": get_shade,
		"scrub": scrub,
		"guess_mimetype": mimetypes.guess_type,
		'html2text': html2text,
		'json': json,
		"dev_server": 1 if os.environ.get('DEV_SERVER', False) else 0
	}

	if not dataent.flags.in_setup_help:
		out['get_visible_columns'] = get_visible_columns
		out['dataent']['date_format'] = date_format
		out['dataent']["db"] = {
			"get_value": dataent.db.get_value,
			"get_default": dataent.db.get_default,
			"escape": dataent.db.escape,
		}

	# load jenv methods from hooks.py
	for method_name, method_definition in get_jenv_customization("methods"):
		out[method_name] = dataent.get_attr(method_definition)

	return out

def get_jloader():
	import dataent
	if not getattr(dataent.local, 'jloader', None):
		from jinja2 import ChoiceLoader, PackageLoader, PrefixLoader

		if dataent.local.flags.in_setup_help:
			apps = ['dataent']
		else:
			apps = dataent.get_hooks('template_apps')
			if not apps:
				apps = dataent.local.flags.web_pages_apps or dataent.get_installed_apps(sort=True)
				apps.reverse()

		if not "dataent" in apps:
			apps.append('dataent')

		dataent.local.jloader = ChoiceLoader(
			# search for something like app/templates/...
			[PrefixLoader(dict(
				(app, PackageLoader(app, ".")) for app in apps
			))]

			# search for something like templates/...
			+ [PackageLoader(app, ".") for app in apps]
		)

	return dataent.local.jloader

def set_filters(jenv):
	import dataent
	from dataent.utils import global_date_format, cint, cstr, flt, markdown
	from dataent.website.utils import get_shade, abs_url

	jenv.filters["global_date_format"] = global_date_format
	jenv.filters["markdown"] = markdown
	jenv.filters["json"] = dataent.as_json
	jenv.filters["get_shade"] = get_shade
	jenv.filters["len"] = len
	jenv.filters["int"] = cint
	jenv.filters["str"] = cstr
	jenv.filters["flt"] = flt
	jenv.filters["abs_url"] = abs_url

	if dataent.flags.in_setup_help: return

	# load jenv_filters from hooks.py
	for filter_name, filter_function in get_jenv_customization("filters"):
		jenv.filters[filter_name] = dataent.get_attr(filter_function)

def get_jenv_customization(customizable_type):
	import dataent

	if getattr(dataent.local, "site", None):
		for app in dataent.get_installed_apps():
			for jenv_customizable, jenv_customizable_definition in dataent.get_hooks(app_name=app).get("jenv", {}).items():
				if customizable_type == jenv_customizable:
					for data in jenv_customizable_definition:
						split_data = data.split(":")
						yield split_data[0], split_data[1]
