# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
import dataent.sessions
from dataent.utils import cstr
import os, mimetypes, json

import six
from six import iteritems
from werkzeug.wrappers import Response
from werkzeug.routing import Map, Rule, NotFound
from werkzeug.wsgi import wrap_file

from dataent.website.context import get_context
from dataent.website.redirect import resolve_redirect
from dataent.website.utils import (get_home_page, can_cache, delete_page_cache,
	get_toc, get_next_link)
from dataent.website.router import clear_sitemap
from dataent.translate import guess_language

class PageNotFoundError(Exception): pass

def render(path=None, http_status_code=None):
	"""render html page"""
	if not path:
		path = dataent.local.request.path

	try:
		path = path.strip('/ ')
		resolve_redirect(path)
		path = resolve_path(path)
		data = None

		# if in list of already known 404s, send it
		if can_cache() and dataent.cache().hget('website_404', dataent.request.url):
			data = render_page('404')
			http_status_code = 404
		elif is_static_file(path):
			return get_static_file_response()
		else:
			try:
				data = render_page_by_language(path)
			except dataent.DoesNotExistError:
				doctype, name = get_doctype_from_path(path)
				if doctype and name:
					path = "printview"
					dataent.local.form_dict.doctype = doctype
					dataent.local.form_dict.name = name
				elif doctype:
					path = "list"
					dataent.local.form_dict.doctype = doctype
				else:
					# 404s are expensive, cache them!
					dataent.cache().hset('website_404', dataent.request.url, True)
					data = render_page('404')
					http_status_code = 404

				if not data:
					try:
						data = render_page(path)
					except dataent.PermissionError as e:
						data, http_status_code = render_403(e, path)

			except dataent.PermissionError as e:
				data, http_status_code = render_403(e, path)

			except dataent.Redirect as e:
				raise e

			except Exception:
				path = "error"
				data = render_page(path)
				http_status_code = 500

		data = add_csrf_token(data)

	except dataent.Redirect:
		return build_response(path, "", 301, {
			"Location": dataent.flags.redirect_location or (dataent.local.response or {}).get('location'),
			"Cache-Control": "no-store, no-cache, must-revalidate"
		})

	return build_response(path, data, http_status_code or 200)

def is_static_file(path):
	if ('.' not in path):
		return False
	extn = path.rsplit('.', 1)[-1]
	if extn in ('html', 'md', 'js', 'xml', 'css', 'txt', 'py'):
		return False

	for app in dataent.get_installed_apps():
		file_path = dataent.get_app_path(app, 'www') + '/' + path
		if os.path.exists(file_path):
			dataent.flags.file_path = file_path
			return True

	return False

def get_static_file_response():
	try:
		f = open(dataent.flags.file_path, 'rb')
	except IOError:
		raise NotFound

	response = Response(wrap_file(dataent.local.request.environ, f), direct_passthrough=True)
	response.mimetype = mimetypes.guess_type(dataent.flags.file_path)[0] or 'application/octet-stream'
	return response

def build_response(path, data, http_status_code, headers=None):
	# build response
	response = Response()
	response.data = set_content_type(response, data, path)
	response.status_code = http_status_code
	response.headers["X-Page-Name"] = path.encode("utf-8")
	response.headers["X-From-Cache"] = dataent.local.response.from_cache or False

	if headers:
		for key, val in iteritems(headers):
			response.headers[key] = val.encode("utf-8")

	return response

def render_page_by_language(path):
	translated_languages = dataent.get_hooks("translated_languages_for_website")
	user_lang = guess_language(translated_languages)
	if translated_languages and user_lang in translated_languages:
		try:
			if path and path != "index":
				lang_path = '{0}/{1}'.format(user_lang, path)
			else:
				lang_path = user_lang # index

			return render_page(lang_path)
		except dataent.DoesNotExistError:
			return render_page(path)

	else:
		return render_page(path)

def render_page(path):
	"""get page html"""
	out = None

	if can_cache():
		# return rendered page
		page_cache = dataent.cache().hget("website_page", path)
		if page_cache and dataent.local.lang in page_cache:
			out = page_cache[dataent.local.lang]

	if out:
		dataent.local.response.from_cache = True
		return out

	return build(path)

def build(path):
	if not dataent.db:
		dataent.connect()

	try:
		return build_page(path)
	except dataent.DoesNotExistError:
		hooks = dataent.get_hooks()
		if hooks.website_catch_all:
			path = hooks.website_catch_all[0]
			return build_page(path)
		else:
			raise

def build_page(path):
	if not getattr(dataent.local, "path", None):
		dataent.local.path = path

	context = get_context(path)

	if context.source:
		html = dataent.render_template(context.source, context)

	elif context.template:
		if path.endswith('min.js'):
			html = dataent.get_jloader().get_source(dataent.get_jenv(), context.template)[0]
		else:
			html = dataent.get_template(context.template).render(context)

	if '{index}' in html:
		html = html.replace('{index}', get_toc(context.route))

	if '{next}' in html:
		html = html.replace('{next}', get_next_link(context.route))

	# html = dataent.get_template(context.base_template_path).render(context)

	if can_cache(context.no_cache):
		page_cache = dataent.cache().hget("website_page", path) or {}
		page_cache[dataent.local.lang] = html
		dataent.cache().hset("website_page", path, page_cache)

	return html

def resolve_path(path):
	if not path:
		path = "index"

	if path.endswith('.html'):
		path = path[:-5]

	if path == "index":
		path = get_home_page()

	dataent.local.path = path

	if path != "index":
		path = resolve_from_map(path)

	return path

def resolve_from_map(path):
	m = Map([Rule(r["from_route"], endpoint=r["to_route"], defaults=r.get("defaults"))
		for r in get_website_rules()])
	urls = m.bind_to_environ(dataent.local.request.environ)
	try:
		endpoint, args = urls.match("/" + path)
		path = endpoint
		if args:
			# don't cache when there's a query string!
			dataent.local.no_cache = 1
			dataent.local.form_dict.update(args)

	except NotFound:
		pass

	return path

def get_website_rules():
	'''Get website route rules from hooks and DocType route'''
	def _get():
		rules = dataent.get_hooks("website_route_rules")
		for d in dataent.get_all('DocType', 'name, route', dict(has_web_view=1)):
			if d.route:
				rules.append(dict(from_route = '/' + d.route.strip('/'), to_route=d.name))

		return rules

	return dataent.cache().get_value('website_route_rules', _get)

def set_content_type(response, data, path):
	if isinstance(data, dict):
		response.mimetype = 'application/json'
		response.charset = 'utf-8'
		data = json.dumps(data)
		return data

	response.mimetype = 'text/html'
	response.charset = 'utf-8'

	if "." in path:
		content_type, encoding = mimetypes.guess_type(path)
		if content_type:
			response.mimetype = content_type
			if encoding:
				response.charset = encoding

	return data

def clear_cache(path=None):
	'''Clear website caches

	:param path: (optional) for the given path'''
	for key in ('website_generator_routes', 'website_pages',
		'website_full_index'):
		dataent.cache().delete_value(key)

	dataent.cache().delete_value("website_404")
	if path:
		dataent.cache().hdel('website_redirects', path)
		delete_page_cache(path)
	else:
		clear_sitemap()
		dataent.clear_cache("Guest")
		for key in ('portal_menu_items', 'home_page', 'website_route_rules',
			'doctypes_with_web_view', 'website_redirects', 'page_context',
			'website_page'):
			dataent.cache().delete_value(key)

	for method in dataent.get_hooks("website_clear_cache"):
		dataent.get_attr(method)(path)

def render_403(e, pathname):
	dataent.local.message = cstr(e.message if six.PY2 else e)
	dataent.local.message_title = _("Not Permitted")
	dataent.local.response['context'] = dict(
		indicator_color = 'red',
		primary_action = '/login',
		primary_label = _('Login'),
		fullpage=True
	)
	return render_page("message"), e.http_status_code

def get_doctype_from_path(path):
	doctypes = dataent.db.sql_list("select name from tabDocType")

	parts = path.split("/")

	doctype = parts[0]
	name = parts[1] if len(parts) > 1 else None

	if doctype in doctypes:
		return doctype, name

	# try scrubbed
	doctype = doctype.replace("_", " ").title()
	if doctype in doctypes:
		return doctype, name

	return None, None

def add_csrf_token(data):
	if dataent.local.session:
		return data.replace("<!-- csrf_token -->", '<script>dataent.csrf_token = "{0}";</script>'.format(
				dataent.local.session.data.csrf_token))
	else:
		return data
