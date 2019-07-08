# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function

from six import iteritems, text_type, string_types, PY2

"""
	dataent.translate
	~~~~~~~~~~~~~~~~

	Translation tools for dataent
"""

import dataent, os, re, io, codecs, json
from dataent.model.utils import render_include, InvalidIncludePath
from dataent.utils import strip, strip_html_tags, is_html
from jinja2 import TemplateError
import itertools, operator

def guess_language(lang_list=None):
	"""Set `dataent.local.lang` from HTTP headers at beginning of request"""
	lang_codes = dataent.request.accept_languages.values()
	if not lang_codes:
		return dataent.local.lang

	guess = None
	if not lang_list:
		lang_list = get_all_languages() or []

	for l in lang_codes:
		code = l.strip()
		if not isinstance(code, text_type):
			code = text_type(code, 'utf-8')
		if code in lang_list or code == "en":
			guess = code
			break

		# check if parent language (pt) is setup, if variant (pt-BR)
		if "-" in code:
			code = code.split("-")[0]
			if code in lang_list:
				guess = code
				break

	return guess or dataent.local.lang

def get_user_lang(user=None):
	"""Set dataent.local.lang from user preferences on session beginning or resumption"""
	if not user:
		user = dataent.session.user

	# via cache
	lang = dataent.cache().hget("lang", user)

	if not lang:

		# if defined in user profile
		lang = dataent.db.get_value("User", user, "language")
		if not lang:
			lang = dataent.db.get_default("lang")

		if not lang:
			lang = dataent.local.lang or 'en'

		dataent.cache().hset("lang", user, lang)

	return lang

def get_lang_code(lang):
	return dataent.db.get_value('Language', {'language_name': lang}) or lang

def set_default_language(lang):
	"""Set Global default language"""
	if dataent.db.get_default("lang") != lang:
		dataent.db.set_default("lang", lang)
	dataent.local.lang = lang

def get_all_languages():
	"""Returns all language codes ar, ch etc"""
	def _get():
		if not dataent.db:
			dataent.connect()
		return dataent.db.sql_list('select name from tabLanguage')
	return dataent.cache().get_value('languages', _get)

def get_lang_dict():
	"""Returns all languages in dict format, full name is the key e.g. `{"english":"en"}`"""
	return dict(dataent.db.sql('select language_name, name from tabLanguage'))

def get_dict(fortype, name=None):
	"""Returns translation dict for a type of object.

	 :param fortype: must be one of `doctype`, `page`, `report`, `include`, `jsfile`, `boot`
	 :param name: name of the document for which assets are to be returned.
	 """
	fortype = fortype.lower()
	cache = dataent.cache()
	asset_key = fortype + ":" + (name or "-")
	translation_assets = cache.hget("translation_assets", dataent.local.lang, shared=True) or {}

	if not asset_key in translation_assets:
		if fortype=="doctype":
			messages = get_messages_from_doctype(name)
		elif fortype=="page":
			messages = get_messages_from_page(name)
		elif fortype=="report":
			messages = get_messages_from_report(name)
		elif fortype=="include":
			messages = get_messages_from_include_files()
		elif fortype=="jsfile":
			messages = get_messages_from_file(name)
		elif fortype=="boot":
			messages = get_messages_from_include_files()
			messages += dataent.db.sql("select 'Print Format:', name from `tabPrint Format`")
			messages += dataent.db.sql("select 'DocType:', name from tabDocType")
			messages += dataent.db.sql("select 'Role:', name from tabRole")
			messages += dataent.db.sql("select 'Module:', name from `tabModule Def`")
			messages += dataent.db.sql("select 'Module:', label from `tabDesktop Icon` where standard=1 or owner=%s",
				dataent.session.user)

		message_dict = make_dict_from_messages(messages)
		message_dict.update(get_dict_from_hooks(fortype, name))

		# remove untranslated
		message_dict = {k:v for k, v in iteritems(message_dict) if k!=v}

		translation_assets[asset_key] = message_dict

		cache.hset("translation_assets", dataent.local.lang, translation_assets, shared=True)

	return translation_assets[asset_key]

def get_dict_from_hooks(fortype, name):
	translated_dict = {}

	hooks = dataent.get_hooks("get_translated_dict")
	for (hook_fortype, fortype_name) in hooks:
		if hook_fortype == fortype and fortype_name == name:
			for method in hooks[(hook_fortype, fortype_name)]:
				translated_dict.update(dataent.get_attr(method)())

	return translated_dict

def add_lang_dict(code):
	"""Extracts messages and returns Javascript code snippet to be appened at the end
	of the given script

	:param code: Javascript code snippet to which translations needs to be appended."""
	messages = extract_messages_from_code(code)
	messages = [message for pos, message in messages]
	code += "\n\n$.extend(dataent._messages, %s)" % json.dumps(make_dict_from_messages(messages))
	return code

def make_dict_from_messages(messages, full_dict=None):
	"""Returns translated messages as a dict in Language specified in `dataent.local.lang`

	:param messages: List of untranslated messages
	"""
	out = {}
	if full_dict==None:
		full_dict = get_full_dict(dataent.local.lang)

	for m in messages:
		if m[1] in full_dict:
			out[m[1]] = full_dict[m[1]]

	return out

def get_lang_js(fortype, name):
	"""Returns code snippet to be appended at the end of a JS script.

	:param fortype: Type of object, e.g. `DocType`
	:param name: Document name
	"""
	return "\n\n$.extend(dataent._messages, %s)" % json.dumps(get_dict(fortype, name))

def get_full_dict(lang):
	"""Load and return the entire translations dictionary for a language from :meth:`frape.cache`

	:param lang: Language Code, e.g. `hi`
	"""
	if not lang:
		return {}

	# found in local, return!
	if getattr(dataent.local, 'lang_full_dict', None) and dataent.local.lang_full_dict.get(lang, None):
		return dataent.local.lang_full_dict

	dataent.local.lang_full_dict = load_lang(lang)

	try:
		# get user specific transaltion data
		user_translations = get_user_translations(lang)
	except Exception:
		user_translations = None

	if user_translations:
		dataent.local.lang_full_dict.update(user_translations)

	return dataent.local.lang_full_dict

def load_lang(lang, apps=None):
	"""Combine all translations from `.csv` files in all `apps`.
	For derivative languages (es-GT), take translations from the
	base language (es) and then update translations from the child (es-GT)"""

	if lang=='en':
		return {}

	out = dataent.cache().hget("lang_full_dict", lang, shared=True)
	if not out:
		out = {}
		for app in (apps or dataent.get_all_apps(True)):
			path = os.path.join(dataent.get_pymodule_path(app), "translations", lang + ".csv")
			out.update(get_translation_dict_from_file(path, lang, app) or {})

		if '-' in lang:
			parent = lang.split('-')[0]
			parent_out = load_lang(parent)
			parent_out.update(out)
			out = parent_out

		dataent.cache().hset("lang_full_dict", lang, out, shared=True)

	return out or {}

def get_translation_dict_from_file(path, lang, app):
	"""load translation dict from given path"""
	cleaned = {}
	if os.path.exists(path):
		csv_content = read_csv_file(path)

		for item in csv_content:
			if len(item)==3:
				# with file and line numbers
				cleaned[item[1]] = strip(item[2])

			elif len(item)==2:
				cleaned[item[0]] = strip(item[1])

			elif item:
				raise Exception("Bad translation in '{app}' for language '{lang}': {values}".format(
					app=app, lang=lang, values=repr(item).encode("utf-8")
				))

	return cleaned

def get_user_translations(lang):
	out = dataent.cache().hget('lang_user_translations', lang)
	if out is None:
		out = {}
		for fields in dataent.get_all('Translation',
			fields= ["source_name", "target_name"], filters={'language': lang}):
				out.update({fields.source_name: fields.target_name})
		dataent.cache().hset('lang_user_translations', lang, out)

	return out


def clear_cache():
	"""Clear all translation assets from :meth:`dataent.cache`"""
	cache = dataent.cache()
	cache.delete_key("langinfo")

	# clear translations saved in boot cache
	cache.delete_key("bootinfo")
	cache.delete_key("lang_full_dict", shared=True)
	cache.delete_key("translation_assets", shared=True)
	cache.delete_key("lang_user_translations")

def get_messages_for_app(app):
	"""Returns all messages (list) for a specified `app`"""
	messages = []
	modules = ", ".join(['"{}"'.format(m.title().replace("_", " ")) \
		for m in dataent.local.app_modules[app]])

	# doctypes
	if modules:
		for name in dataent.db.sql_list("""select name from tabDocType
			where module in ({})""".format(modules)):
			messages.extend(get_messages_from_doctype(name))

		# pages
		for name, title in dataent.db.sql("""select name, title from tabPage
			where module in ({})""".format(modules)):
			messages.append((None, title or name))
			messages.extend(get_messages_from_page(name))


		# reports
		for name in dataent.db.sql_list("""select tabReport.name from tabDocType, tabReport
			where tabReport.ref_doctype = tabDocType.name
				and tabDocType.module in ({})""".format(modules)):
			messages.append((None, name))
			messages.extend(get_messages_from_report(name))
			for i in messages:
				if not isinstance(i, tuple):
					raise Exception

	# workflow based on app.hooks.fixtures
	messages.extend(get_messages_from_workflow(app_name=app))

	# custom fields based on app.hooks.fixtures
	messages.extend(get_messages_from_custom_fields(app_name=app))

	# app_include_files
	messages.extend(get_all_messages_from_js_files(app))

	# server_messages
	messages.extend(get_server_messages(app))
	return deduplicate_messages(messages)

def get_messages_from_doctype(name):
	"""Extract all translatable messages for a doctype. Includes labels, Python code,
	Javascript code, html templates"""
	messages = []
	meta = dataent.get_meta(name)

	messages = [meta.name, meta.module]

	if meta.description:
		messages.append(meta.description)

	# translations of field labels, description and options
	for d in meta.get("fields"):
		messages.extend([d.label, d.description])

		if d.fieldtype=='Select' and d.options:
			options = d.options.split('\n')
			if not "icon" in options[0]:
				messages.extend(options)

	# translations of roles
	for d in meta.get("permissions"):
		if d.role:
			messages.append(d.role)

	messages = [message for message in messages if message]
	messages = [('DocType: ' + name, message) for message in messages if is_translatable(message)]

	# extract from js, py files
	if not meta.custom:
		doctype_file_path = dataent.get_module_path(meta.module, "doctype", meta.name, meta.name)
		messages.extend(get_messages_from_file(doctype_file_path + ".js"))
		messages.extend(get_messages_from_file(doctype_file_path + "_list.js"))
		messages.extend(get_messages_from_file(doctype_file_path + "_list.html"))
		messages.extend(get_messages_from_file(doctype_file_path + "_calendar.js"))
		messages.extend(get_messages_from_file(doctype_file_path + "_dashboard.html"))

	# workflow based on doctype
	messages.extend(get_messages_from_workflow(doctype=name))

	return messages

def get_messages_from_workflow(doctype=None, app_name=None):
	assert doctype or app_name, 'doctype or app_name should be provided'

	# translations for Workflows
	workflows = []
	if doctype:
		workflows = dataent.get_all('Workflow', filters={'document_type': doctype})
	else:
		fixtures = dataent.get_hooks('fixtures', app_name=app_name) or []
		for fixture in fixtures:
			if isinstance(fixture, string_types) and fixture == 'Worflow':
				workflows = dataent.get_all('Workflow')
				break
			elif isinstance(fixture, dict) and fixture.get('dt', fixture.get('doctype')) == 'Workflow':
				workflows.extend(dataent.get_all('Workflow', filters=fixture.get('filters')))

	messages  = []
	for w in workflows:
		states = dataent.db.sql(
			'select distinct state from `tabWorkflow Document State` where parent=%s',
			(w['name'],), as_dict=True)

		messages.extend([('Workflow: ' + w['name'], state['state']) for state in states if is_translatable(state['state'])])

		states = dataent.db.sql(
			'select distinct message from `tabWorkflow Document State` where parent=%s and message is not null',
			(w['name'],), as_dict=True)

		messages.extend([("Workflow: " + w['name'], state['message'])
			for state in states if is_translatable(state['message'])])

		actions = dataent.db.sql(
			'select distinct action from `tabWorkflow Transition` where parent=%s',
			(w['name'],), as_dict=True)

		messages.extend([("Workflow: " + w['name'], action['action']) \
			for action in actions if is_translatable(action['action'])])

	return messages


def get_messages_from_custom_fields(app_name):
	fixtures = dataent.get_hooks('fixtures', app_name=app_name) or []
	custom_fields = []

	for fixture in fixtures:
		if isinstance(fixture, string_types) and fixture == 'Custom Field':
			custom_fields = dataent.get_all('Custom Field', fields=['name','label', 'description', 'fieldtype', 'options'])
			break
		elif isinstance(fixture, dict) and fixture.get('dt', fixture.get('doctype')) == 'Custom Field':
			custom_fields.extend(dataent.get_all('Custom Field', filters=fixture.get('filters'),
				fields=['name','label', 'description', 'fieldtype', 'options']))

	messages = []
	for cf in custom_fields:
		for prop in ('label', 'description'):
			if not cf.get(prop) or not is_translatable(cf[prop]):
				continue
			messages.append(('Custom Field - {}: {}'.format(prop, cf['name']), cf[prop]))
		if cf['fieldtype'] == 'Selection' and cf.get('options'):
			for option in cf['options'].split('\n'):
				if option and 'icon' not in option and is_translatable(option):
					messages.append(('Custom Field - Description: ' + cf['name'], option))

	return messages

def get_messages_from_page(name):
	"""Returns all translatable strings from a :class:`dataent.core.doctype.Page`"""
	return _get_messages_from_page_or_report("Page", name)

def get_messages_from_report(name):
	"""Returns all translatable strings from a :class:`dataent.core.doctype.Report`"""
	report = dataent.get_doc("Report", name)
	messages = _get_messages_from_page_or_report("Report", name,
		dataent.db.get_value("DocType", report.ref_doctype, "module"))
	# TODO position here!
	if report.query:
		messages.extend([(None, message) for message in re.findall('"([^:,^"]*):', report.query) if is_translatable(message)])
	messages.append((None,report.report_name))
	return messages

def _get_messages_from_page_or_report(doctype, name, module=None):
	if not module:
		module = dataent.db.get_value(doctype, name, "module")

	doc_path = dataent.get_module_path(module, doctype, name)

	messages = get_messages_from_file(os.path.join(doc_path, dataent.scrub(name) +".py"))

	if os.path.exists(doc_path):
		for filename in os.listdir(doc_path):
			if filename.endswith(".js") or filename.endswith(".html"):
				messages += get_messages_from_file(os.path.join(doc_path, filename))

	return messages

def get_server_messages(app):
	"""Extracts all translatable strings (tagged with :func:`dataent._`) from Python modules
		inside an app"""
	messages = []
	file_extensions = ('.py', '.html', '.js', '.vue')
	for basepath, folders, files in os.walk(dataent.get_pymodule_path(app)):
		for dontwalk in (".git", "public", "locale"):
			if dontwalk in folders: folders.remove(dontwalk)

		for f in files:
			f = dataent.as_unicode(f)
			if f.endswith(file_extensions):
				messages.extend(get_messages_from_file(os.path.join(basepath, f)))

	return messages

def get_messages_from_include_files(app_name=None):
	"""Returns messages from js files included at time of boot like desk.min.js for desk and web"""
	messages = []
	for file in (dataent.get_hooks("app_include_js", app_name=app_name) or []) + (dataent.get_hooks("web_include_js", app_name=app_name) or []):
		messages.extend(get_messages_from_file(os.path.join(dataent.local.sites_path, file)))

	return messages

def get_all_messages_from_js_files(app_name=None):
	"""Extracts all translatable strings from app `.js` files"""
	messages = []
	for app in ([app_name] if app_name else dataent.get_installed_apps()):
		if os.path.exists(dataent.get_app_path(app, "public")):
			for basepath, folders, files in os.walk(dataent.get_app_path(app, "public")):
				if "dataent/public/js/lib" in basepath:
					continue

				for fname in files:
					if fname.endswith(".js") or fname.endswith(".html"):
						messages.extend(get_messages_from_file(os.path.join(basepath, fname)))

	return messages

def get_messages_from_file(path):
	"""Returns a list of transatable strings from a code file

	:param path: path of the code file
	"""
	apps_path = get_bench_dir()
	if os.path.exists(path):
		with open(path, 'r') as sourcefile:
			return [(os.path.relpath(" +".join([path, str(pos)]), apps_path),
					message) for pos, message in  extract_messages_from_code(sourcefile.read(), path.endswith(".py"))]
	else:
		# print "Translate: {0} missing".format(os.path.abspath(path))
		return []

def extract_messages_from_code(code, is_py=False):
	"""Extracts translatable srings from a code file

	:param code: code from which translatable files are to be extracted
	:param is_py: include messages in triple quotes e.g. `_('''message''')`"""
	try:
		code = dataent.as_unicode(render_include(code))
	except (TemplateError, ImportError, InvalidIncludePath):
		# Exception will occur when it encounters John Resig's microtemplating code
		pass

	messages = []
	messages += [(m.start(), m.groups()[0]) for m in re.compile('_\("([^"]*)"').finditer(code)]
	messages += [(m.start(), m.groups()[0]) for m in re.compile("_\('([^']*)'").finditer(code)]
	if is_py:
		messages += [(m.start(), m.groups()[0]) for m in re.compile('_\("{3}([^"]*)"{3}.*\)').finditer(code)]

	messages = [(pos, message) for pos, message in messages if is_translatable(message)]
	return pos_to_line_no(messages, code)

def is_translatable(m):
	if re.search("[a-zA-Z]", m) and not m.startswith("fa fa-") and not m.endswith("px") and not m.startswith("eval:"):
		return True
	return False

def pos_to_line_no(messages, code):
	ret = []
	messages = sorted(messages, key=lambda x: x[0])
	newlines = [m.start() for m in re.compile('\\n').finditer(code)]
	line = 1
	newline_i = 0
	for pos, message in messages:
		while newline_i < len(newlines) and pos > newlines[newline_i]:
			line+=1
			newline_i+= 1
		ret.append((line, message))
	return ret

def read_csv_file(path):
	"""Read CSV file and return as list of list

	:param path: File path"""
	from csv import reader

	if PY2:
		with codecs.open(path, 'r', 'utf-8') as msgfile:
			data = msgfile.read()

			# for japanese! #wtf
			data = data.replace(chr(28), "").replace(chr(29), "")
			data = reader([r.encode('utf-8') for r in data.splitlines()])
			newdata = [[text_type(val, 'utf-8') for val in row] for row in data]
	else:
		with io.open(path, mode='r', encoding='utf-8', newline='') as msgfile:
			data = reader(msgfile)
			newdata = [[ val for val in row ] for row in data]
	return newdata

def write_csv_file(path, app_messages, lang_dict):
	"""Write translation CSV file.

	:param path: File path, usually `[app]/translations`.
	:param app_messages: Translatable strings for this app.
	:param lang_dict: Full translated dict.
	"""
	app_messages.sort(key = lambda x: x[1])
	from csv import writer
	with open(path, 'wb') as msgfile:
		w = writer(msgfile, lineterminator='\n')
		for p, m in app_messages:
			t = lang_dict.get(m, '')
			# strip whitespaces
			t = re.sub('{\s?([0-9]+)\s?}', "{\g<1>}", t)
			w.writerow([p.encode('utf-8') if p else '', m.encode('utf-8'), t.encode('utf-8')])

def get_untranslated(lang, untranslated_file, get_all=False):
	"""Returns all untranslated strings for a language and writes in a file

	:param lang: Language code.
	:param untranslated_file: Output file path.
	:param get_all: Return all strings, translated or not."""
	clear_cache()
	apps = dataent.get_all_apps(True)

	messages = []
	untranslated = []
	for app in apps:
		messages.extend(get_messages_for_app(app))

	messages = deduplicate_messages(messages)

	def escape_newlines(s):
		return (s.replace("\\\n", "|||||")
				.replace("\\n", "||||")
				.replace("\n", "|||"))

	if get_all:
		print(str(len(messages)) + " messages")
		with open(untranslated_file, "w") as f:
			for m in messages:
				# replace \n with ||| so that internal linebreaks don't get split
				f.write((escape_newlines(m[1]) + os.linesep).encode("utf-8"))
	else:
		full_dict = get_full_dict(lang)

		for m in messages:
			if not full_dict.get(m[1]):
				untranslated.append(m[1])

		if untranslated:
			print(str(len(untranslated)) + " missing translations of " + str(len(messages)))
			with open(untranslated_file, "w") as f:
				for m in untranslated:
					# replace \n with ||| so that internal linebreaks don't get split
					f.write((escape_newlines(m) + os.linesep).encode("utf-8"))
		else:
			print("all translated!")

def update_translations(lang, untranslated_file, translated_file):
	"""Update translations from a source and target file for a given language.

	:param lang: Language code (e.g. `en`).
	:param untranslated_file: File path with the messages in English.
	:param translated_file: File path with messages in language to be updated."""
	clear_cache()
	full_dict = get_full_dict(lang)

	def restore_newlines(s):
		return (s.replace("|||||", "\\\n")
				.replace("| | | | |", "\\\n")
				.replace("||||", "\\n")
				.replace("| | | |", "\\n")
				.replace("|||", "\n")
				.replace("| | |", "\n"))

	translation_dict = {}
	for key, value in zip(dataent.get_file_items(untranslated_file, ignore_empty_lines=False),
		dataent.get_file_items(translated_file, ignore_empty_lines=False)):

		# undo hack in get_untranslated
		translation_dict[restore_newlines(key)] = restore_newlines(value)

	full_dict.update(translation_dict)

	for app in dataent.get_all_apps(True):
		write_translations_file(app, lang, full_dict)

def import_translations(lang, path):
	"""Import translations from file in standard format"""
	clear_cache()
	full_dict = get_full_dict(lang)
	full_dict.update(get_translation_dict_from_file(path, lang, 'import'))

	for app in dataent.get_all_apps(True):
		write_translations_file(app, lang, full_dict)


def rebuild_all_translation_files():
	"""Rebuild all translation files: `[app]/translations/[lang].csv`."""
	for lang in get_all_languages():
		for app in dataent.get_all_apps():
			write_translations_file(app, lang)

def write_translations_file(app, lang, full_dict=None, app_messages=None):
	"""Write a translation file for a given language.

	:param app: `app` for which translations are to be written.
	:param lang: Language code.
	:param full_dict: Full translated language dict (optional).
	:param app_messages: Source strings (optional).
	"""
	if not app_messages:
		app_messages = get_messages_for_app(app)

	if not app_messages:
		return

	tpath = dataent.get_pymodule_path(app, "translations")
	dataent.create_folder(tpath)
	write_csv_file(os.path.join(tpath, lang + ".csv"),
		app_messages, full_dict or get_full_dict(lang))

def send_translations(translation_dict):
	"""Append translated dict in `dataent.local.response`"""
	if "__messages" not in dataent.local.response:
		dataent.local.response["__messages"] = {}

	dataent.local.response["__messages"].update(translation_dict)

def deduplicate_messages(messages):
	ret = []
	op = operator.itemgetter(1)
	messages = sorted(messages, key=op)
	for k, g in itertools.groupby(messages, op):
		ret.append(next(g))
	return ret

def get_bench_dir():
	return os.path.join(dataent.__file__, '..', '..', '..', '..')

def rename_language(old_name, new_name):
	if not dataent.db.exists('Language', new_name):
		return

	language_in_system_settings = dataent.db.get_single_value("System Settings", "language")
	if language_in_system_settings == old_name:
		dataent.db.set_value("System Settings", "System Settings", "language", new_name)

	dataent.db.sql("""update `tabUser` set language=%(new_name)s where language=%(old_name)s""",
		{ "old_name": old_name, "new_name": new_name })

@dataent.whitelist()
def update_translations_for_source(source=None, translation_dict=None):
	if not (source and translation_dict):
		return

	translation_dict = json.loads(translation_dict)

	# for existing records
	translation_records = dataent.db.get_values('Translation', { 'source_name': source }, ['name', 'language'],  as_dict=1)
	for d in translation_records:
		if translation_dict.get(d.language, None):
			doc = dataent.get_doc('Translation', d.name)
			doc.target_name = translation_dict.get(d.language)
			doc.save()
			# done with this lang value
			translation_dict.pop(d.language)
		else:
			dataent.delete_doc('Translation', d.name)

	# remaining values are to be inserted
	for lang, target_name in iteritems(translation_dict):
		doc = dataent.new_doc('Translation')
		doc.language = lang
		doc.source_name = source
		doc.target_name = target_name
		doc.save()

	return translation_records

@dataent.whitelist()
def get_translations(source_name):
	if is_html(source_name):
		source_name = strip_html_tags(source_name)

	return dataent.db.get_list('Translation',
		fields = ['name', 'language', 'target_name as translation'],
		filters = {
			'source_name': source_name
		}
	)