# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

from six import iteritems, text_type

"""
bootstrap client session
"""

import dataent
import dataent.defaults
import dataent.desk.desk_page
from dataent.desk.form.load import get_meta_bundle
from dataent.utils.change_log import get_versions
from dataent.translate import get_lang_dict
from dataent.email.inbox import get_email_accounts
from dataent.core.doctype.feedback_trigger.feedback_trigger import get_enabled_feedback_trigger

def get_bootinfo():
	"""build and return boot info"""
	dataent.set_user_lang(dataent.session.user)
	bootinfo = dataent._dict()
	hooks = dataent.get_hooks()
	doclist = []

	# user
	get_user(bootinfo)

	# system info
	bootinfo.sitename = dataent.local.site
	bootinfo.sysdefaults = dataent.defaults.get_defaults()
	bootinfo.server_date = dataent.utils.nowdate()

	if dataent.session['user'] != 'Guest':
		bootinfo.user_info = get_fullnames()
		bootinfo.sid = dataent.session['sid']

	bootinfo.modules = {}
	bootinfo.module_list = []
	load_desktop_icons(bootinfo)
	bootinfo.letter_heads = get_letter_heads()
	bootinfo.active_domains = dataent.get_active_domains()
	bootinfo.all_domains = [d.get("name") for d in dataent.get_all("Domain")]

	bootinfo.module_app = dataent.local.module_app
	bootinfo.single_types = [d.name for d in dataent.get_all('DocType', {'issingle': 1})]
	bootinfo.nested_set_doctypes = [d.parent for d in dataent.get_all('DocField', {'fieldname': 'lft'}, ['parent'])]
	add_home_page(bootinfo, doclist)
	bootinfo.page_info = get_allowed_pages()
	load_translations(bootinfo)
	add_timezone_info(bootinfo)
	load_conf_settings(bootinfo)
	load_print(bootinfo, doclist)
	doclist.extend(get_meta_bundle("Page"))
	bootinfo.home_folder = dataent.db.get_value("File", {"is_home_folder": 1})

	# ipinfo
	if dataent.session.data.get('ipinfo'):
		bootinfo.ipinfo = dataent.session['data']['ipinfo']

	# add docs
	bootinfo.docs = doclist

	for method in hooks.boot_session or []:
		dataent.get_attr(method)(bootinfo)

	if bootinfo.lang:
		bootinfo.lang = text_type(bootinfo.lang)
	bootinfo.versions = {k: v['version'] for k, v in get_versions().items()}

	bootinfo.error_report_email = dataent.conf.error_report_email
	bootinfo.calendars = sorted(dataent.get_hooks("calendars"))
	bootinfo.treeviews = dataent.get_hooks("treeviews") or []
	bootinfo.lang_dict = get_lang_dict()
	bootinfo.feedback_triggers = get_enabled_feedback_trigger()
	bootinfo.gsuite_enabled = get_gsuite_status()
	bootinfo.success_action = get_success_action()
	bootinfo.update(get_email_accounts(user=dataent.session.user))

	return bootinfo

def get_letter_heads():
	letter_heads = {}
	for letter_head in dataent.get_all("Letter Head", fields = ["name", "content", "footer"]):
		letter_heads.setdefault(letter_head.name,
			{'header': letter_head.content, 'footer': letter_head.footer})

	return letter_heads

def load_conf_settings(bootinfo):
	from dataent import conf
	bootinfo.max_file_size = conf.get('max_file_size') or 10485760
	for key in ('developer_mode', 'socketio_port', 'file_watcher_port'):
		if key in conf: bootinfo[key] = conf.get(key)

def load_desktop_icons(bootinfo):
	from dataent.desk.doctype.desktop_icon.desktop_icon import get_desktop_icons
	bootinfo.desktop_icons = get_desktop_icons()

def get_allowed_pages():
	return get_user_pages_or_reports('Page')

def get_allowed_reports():
	return get_user_pages_or_reports('Report')

def get_user_pages_or_reports(parent):
	roles = dataent.get_roles()
	has_role = {}
	column = get_column(parent)

	# get pages or reports set on custom role
	custom_roles = dataent.db.sql("""
		select
			`tabCustom Role`.{field} as name,
			`tabCustom Role`.modified,
			`tabCustom Role`.ref_doctype
		from `tabCustom Role`, `tabHas Role`
		where
			`tabHas Role`.parent = `tabCustom Role`.name
			and `tabCustom Role`.{field} is not null
			and `tabHas Role`.role in ({roles})
	""".format(field=parent.lower(), roles = ', '.join(['%s']*len(roles))), roles, as_dict=1)

	for p in custom_roles:
		has_role[p.name] = {"modified":p.modified, "title": p.name, "ref_doctype": p.ref_doctype}

	standard_roles = dataent.db.sql("""
		select distinct
			tab{parent}.name,
			tab{parent}.modified,
			{column}
		from `tabHas Role`, `tab{parent}`
		where
			`tabHas Role`.role in ({roles})
			and `tabHas Role`.parent = `tab{parent}`.name
			and tab{parent}.name not in (
				select `tabCustom Role`.{field} from `tabCustom Role`
				where `tabCustom Role`.{field} is not null)
			{condition}
		""".format(parent=parent, column=column, roles = ', '.join(['%s']*len(roles)),
			field=parent.lower(), condition="and tabReport.disabled=0" if parent == "Report" else ""),
			roles, as_dict=True)

	for p in standard_roles:
		if p.name not in has_role:
			has_role[p.name] = {"modified":p.modified, "title": p.title}
			if parent == "Report":
				has_role[p.name].update({'ref_doctype': p.ref_doctype})

	# pages with no role are allowed
	if parent =="Page":
		pages_with_no_roles = dataent.db.sql("""
			select
				`tab{parent}`.name, `tab{parent}`.modified, {column}
			from `tab{parent}`
			where
				(select count(*) from `tabHas Role`
				where `tabHas Role`.parent=tab{parent}.name) = 0
		""".format(parent=parent, column=column), as_dict=1)

		for p in pages_with_no_roles:
			if p.name not in has_role:
				has_role[p.name] = {"modified": p.modified, "title": p.title}

	elif parent == "Report":
		for report_name in has_role:
			has_role[report_name]["report_type"] = dataent.db.get_value("Report", report_name, "report_type")

	return has_role

def get_column(doctype):
	column = "`tabPage`.title as title"
	if doctype == "Report":
		column = "`tabReport`.name as name, `tabReport`.name as title, `tabReport`.ref_doctype, `tabReport`.report_type"

	return column

def load_translations(bootinfo):
	messages = dataent.get_lang_dict("boot")

	bootinfo["lang"] = dataent.lang

	# load translated report names
	for name in bootinfo.user.all_reports:
		messages[name] = dataent._(name)

	# only untranslated
	messages = {k:v for k, v in iteritems(messages) if k!=v}

	bootinfo["__messages"] = messages

def get_fullnames():
	"""map of user fullnames"""
	ret = dataent.db.sql("""select name, full_name as fullname,
			user_image as image, gender, email, username
		from tabUser where enabled=1 and user_type!="Website User" """, as_dict=1)

	d = {}
	for r in ret:
		# if not r.image:
		# 	r.image = get_gravatar(r.name)
		d[r.name] = r

	return d

def get_user(bootinfo):
	"""get user info"""
	bootinfo.user = dataent.get_user().load_user()

def add_home_page(bootinfo, docs):
	"""load home page"""
	if dataent.session.user=="Guest":
		return
	home_page = dataent.db.get_default("desktop:home_page")

	if home_page == "setup-wizard":
		bootinfo.setup_wizard_requires = dataent.get_hooks("setup_wizard_requires")

	try:
		page = dataent.desk.desk_page.get(home_page)
	except (dataent.DoesNotExistError, dataent.PermissionError):
		if dataent.message_log:
			dataent.message_log.pop()
		page = dataent.desk.desk_page.get('desktop')

	bootinfo['home_page'] = page.name
	docs.append(page)

def add_timezone_info(bootinfo):
	system = bootinfo.sysdefaults.get("time_zone")
	import dataent.utils.momentjs
	bootinfo.timezone_info = {"zones":{}, "rules":{}, "links":{}}
	dataent.utils.momentjs.update(system, bootinfo.timezone_info)

def load_print(bootinfo, doclist):
	print_settings = dataent.db.get_singles_dict("Print Settings")
	print_settings.doctype = ":Print Settings"
	doclist.append(print_settings)
	load_print_css(bootinfo, print_settings)

def load_print_css(bootinfo, print_settings):
	import dataent.www.printview
	bootinfo.print_css = dataent.www.printview.get_print_style(print_settings.print_style or "Modern", for_legacy=True)

def get_unseen_notes():
	return dataent.db.sql('''select name, title, content, notify_on_every_login from tabNote where notify_on_login=1
		and expire_notification_on > %s and %s not in
			(select user from `tabNote Seen By` nsb
				where nsb.parent=tabNote.name)''', (dataent.utils.now(), dataent.session.user), as_dict=True)

def get_gsuite_status():
	return (dataent.get_value('Gsuite Settings', None, 'enable') == '1')

def get_success_action():
	return dataent.get_all("Success Action", fields=["*"])
