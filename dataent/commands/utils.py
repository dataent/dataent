# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function
import click
import json, os, sys, subprocess
from distutils.spawn import find_executable
import dataent
from dataent.commands import pass_context, get_site
from dataent.utils import update_progress_bar, get_bench_path
from dataent.utils.response import json_handler
from coverage import Coverage
import cProfile, pstats
from six import StringIO

@click.command('build')
@click.option('--app', help='Build assets for app')
@click.option('--make-copy', is_flag=True, default=False, help='Copy the files instead of symlinking')
@click.option('--restore', is_flag=True, default=False, help='Copy the files instead of symlinking with force')
@click.option('--verbose', is_flag=True, default=False, help='Verbose')
def build(app=None, make_copy=False, restore = False, verbose=False):
	"Minify + concatenate JS and CSS files, build translations"
	import dataent.build
	import dataent
	dataent.init('')
	# don't minify in developer_mode for faster builds
	no_compress = dataent.local.conf.developer_mode or False
	dataent.build.bundle(no_compress, app=app, make_copy=make_copy, restore = restore, verbose=verbose)

@click.command('watch')
def watch():
	"Watch and concatenate JS and CSS files as and when they change"
	# if os.environ.get('CI'):
	# 	return
	import dataent.build
	dataent.init('')
	dataent.build.watch(True)

@click.command('clear-cache')
@pass_context
def clear_cache(context):
	"Clear cache, doctype cache and defaults"
	import dataent.sessions
	import dataent.website.render
	from dataent.desk.notifications import clear_notifications
	for site in context.sites:
		try:
			dataent.connect(site)
			dataent.clear_cache()
			clear_notifications()
			dataent.website.render.clear_cache()
		finally:
			dataent.destroy()

@click.command('clear-website-cache')
@pass_context
def clear_website_cache(context):
	"Clear website cache"
	import dataent.website.render
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			dataent.website.render.clear_cache()
		finally:
			dataent.destroy()

@click.command('destroy-all-sessions')
@click.option('--reason')
@pass_context
def destroy_all_sessions(context, reason=None):
	"Clear sessions of all users (logs them out)"
	import dataent.sessions
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			dataent.sessions.clear_all_sessions(reason)
			dataent.db.commit()
		finally:
			dataent.destroy()


@click.command('reset-perms')
@pass_context
def reset_perms(context):
	"Reset permissions for all doctypes"
	from dataent.permissions import reset_perms
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			for d in dataent.db.sql_list("""select name from `tabDocType`
				where istable=0 and custom=0"""):
					dataent.clear_cache(doctype=d)
					reset_perms(d)
		finally:
			dataent.destroy()

@click.command('execute')
@click.argument('method')
@click.option('--args')
@click.option('--kwargs')
@click.option('--profile', is_flag=True, default=False)
@pass_context
def execute(context, method, args=None, kwargs=None, profile=False):
	"Execute a function"
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()

			if args:
				try:
					args = eval(args)
				except NameError:
					args = [args]
			else:
				args = ()

			if kwargs:
				kwargs = eval(kwargs)
			else:
				kwargs = {}

			if profile:
				pr = cProfile.Profile()
				pr.enable()

			ret = dataent.get_attr(method)(*args, **kwargs)

			if profile:
				pr.disable()
				s = StringIO()
				pstats.Stats(pr, stream=s).sort_stats('cumulative').print_stats(.5)
				print(s.getvalue())

			if dataent.db:
				dataent.db.commit()
		finally:
			dataent.destroy()
		if ret:
			print(json.dumps(ret, default=json_handler))


@click.command('add-to-email-queue')
@click.argument('email-path')
@pass_context
def add_to_email_queue(context, email_path):
	"Add an email to the Email Queue"
	site = get_site(context)

	if os.path.isdir(email_path):
		with dataent.init_site(site):
			dataent.connect()
			for email in os.listdir(email_path):
				with open(os.path.join(email_path, email)) as email_data:
					kwargs = json.load(email_data)
					kwargs['delayed'] = True
					dataent.sendmail(**kwargs)
					dataent.db.commit()


@click.command('export-doc')
@click.argument('doctype')
@click.argument('docname')
@pass_context
def export_doc(context, doctype, docname):
	"Export a single document to csv"
	import dataent.modules
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			dataent.modules.export_doc(doctype, docname)
		finally:
			dataent.destroy()

@click.command('export-json')
@click.argument('doctype')
@click.argument('path')
@click.option('--name', help='Export only one document')
@pass_context
def export_json(context, doctype, path, name=None):
	"Export doclist as json to the given path, use '-' as name for Singles."
	from dataent.core.doctype.data_import import data_import
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			data_import.export_json(doctype, path, name=name)
		finally:
			dataent.destroy()

@click.command('export-csv')
@click.argument('doctype')
@click.argument('path')
@pass_context
def export_csv(context, doctype, path):
	"Export data import template with data for DocType"
	from dataent.core.doctype.data_import import data_import
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			data_import.export_csv(doctype, path)
		finally:
			dataent.destroy()

@click.command('export-fixtures')
@pass_context
def export_fixtures(context):
	"Export fixtures"
	from dataent.utils.fixtures import export_fixtures
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			export_fixtures()
		finally:
			dataent.destroy()

@click.command('import-doc')
@click.argument('path')
@pass_context
def import_doc(context, path, force=False):
	"Import (insert/update) doclist. If the argument is a directory, all files ending with .json are imported"
	from dataent.core.doctype.data_import import data_import

	if not os.path.exists(path):
		path = os.path.join('..', path)
	if not os.path.exists(path):
		print('Invalid path {0}'.format(path))
		sys.exit(1)

	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			data_import.import_doc(path, overwrite=context.force)
		finally:
			dataent.destroy()

@click.command('import-csv')
@click.argument('path')
@click.option('--only-insert', default=False, is_flag=True, help='Do not overwrite existing records')
@click.option('--submit-after-import', default=False, is_flag=True, help='Submit document after importing it')
@click.option('--ignore-encoding-errors', default=False, is_flag=True, help='Ignore encoding errors while coverting to unicode')
@click.option('--no-email', default=True, is_flag=True, help='Send email if applicable')

@pass_context
def import_csv(context, path, only_insert=False, submit_after_import=False, ignore_encoding_errors=False, no_email=True):
	"Import CSV using data import"
	from dataent.core.doctype.data_import import importer
	from dataent.utils.csvutils import read_csv_content
	site = get_site(context)

	if not os.path.exists(path):
		path = os.path.join('..', path)
	if not os.path.exists(path):
		print('Invalid path {0}'.format(path))
		sys.exit(1)

	with open(path, 'r') as csvfile:
		content = read_csv_content(csvfile.read())

	dataent.init(site=site)
	dataent.connect()

	try:
		importer.upload(content, submit_after_import=submit_after_import, no_email=no_email,
			ignore_encoding_errors=ignore_encoding_errors, overwrite=not only_insert,
			via_console=True)
		dataent.db.commit()
	except Exception:
		print(dataent.get_traceback())

	dataent.destroy()

@click.command('bulk-rename')
@click.argument('doctype')
@click.argument('path')
@pass_context
def _bulk_rename(context, doctype, path):
	"Rename multiple records via CSV file"
	from dataent.model.rename_doc import bulk_rename
	from dataent.utils.csvutils import read_csv_content

	site = get_site(context)

	with open(path, 'r') as csvfile:
		rows = read_csv_content(csvfile.read())

	dataent.init(site=site)
	dataent.connect()

	bulk_rename(doctype, rows, via_console = True)

	dataent.destroy()

@click.command('mysql')
def mysql():
	"""
		Deprecated
	"""
	click.echo("""
mysql command is deprecated.
Did you mean "bench mariadb"?
""")

@click.command('mariadb')
@pass_context
def mariadb(context):
	"""
		Enter into mariadb console for a given site.
	"""
	import os

	site  = get_site(context)
	dataent.init(site=site)

	# This is assuming you're within the bench instance.
	mysql = find_executable('mysql')
	os.execv(mysql, [
		mysql,
		'-u', dataent.conf.db_name,
		'-p'+dataent.conf.db_password,
		dataent.conf.db_name,
		'-h', dataent.conf.db_host or "localhost",
		'--pager=less -SFX',
		"-A"])

@click.command('jupyter')
@pass_context
def jupyter(context):
	try:
		from pip import main
	except ImportError:
		from pip._internal import main

	reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
	installed_packages = [r.decode().split('==')[0] for r in reqs.split()]
	if 'jupyter' not in installed_packages:
		main(['install', 'jupyter'])
	site = get_site(context)
	dataent.init(site=site)
	jupyter_notebooks_path = os.path.abspath(dataent.get_site_path('jupyter_notebooks'))
	sites_path = os.path.abspath(dataent.get_site_path('..'))
	try:
		os.stat(jupyter_notebooks_path)
	except OSError:
		print('Creating folder to keep jupyter notebooks at {}'.format(jupyter_notebooks_path))
		os.mkdir(jupyter_notebooks_path)
	bin_path = os.path.abspath('../env/bin')
	print('''
Stating Jupyter notebook
Run the following in your first cell to connect notebook to dataent
```
import dataent
dataent.init(site='{site}', sites_path='{sites_path}')
dataent.connect()
dataent.local.lang = dataent.db.get_default('lang')
dataent.db.connect()
```
	'''.format(site=site, sites_path=sites_path))
	os.execv('{0}/jupyter'.format(bin_path), [
		'{0}/jupyter'.format(bin_path),
		'notebook',
		jupyter_notebooks_path,
	])

@click.command('console')
@pass_context
def console(context):
	"Start ipython console for a site"
	site = get_site(context)
	dataent.init(site=site)
	dataent.connect()
	dataent.local.lang = dataent.db.get_default("lang")
	import IPython
	IPython.embed(display_banner = "")

@click.command('run-tests')
@click.option('--app', help="For App")
@click.option('--doctype', help="For DocType")
@click.option('--doctype-list-path', help="Path to .txt file for list of doctypes. Example epaas/tests/server/agriculture.txt")
@click.option('--test', multiple=True, help="Specific test")
@click.option('--driver', help="For Travis")
@click.option('--ui-tests', is_flag=True, default=False, help="Run UI Tests")
@click.option('--module', help="Run tests in a module")
@click.option('--profile', is_flag=True, default=False)
@click.option('--coverage', is_flag=True, default=False)
@click.option('--skip-test-records', is_flag=True, default=False, help="Don't create test records")
@click.option('--skip-before-tests', is_flag=True, default=False, help="Don't run before tests hook")
@click.option('--junit-xml-output', help="Destination file path for junit xml report")
@click.option('--failfast', is_flag=True, default=False)
@pass_context
def run_tests(context, app=None, module=None, doctype=None, test=(),
	driver=None, profile=False, coverage=False, junit_xml_output=False, ui_tests = False,
	doctype_list_path=None, skip_test_records=False, skip_before_tests=False, failfast=False):

	"Run tests"
	import dataent.test_runner
	tests = test

	site = get_site(context)
	dataent.init(site=site)

	dataent.flags.skip_before_tests = skip_before_tests
	dataent.flags.skip_test_records = skip_test_records

	if coverage:
		# Generate coverage report only for app that is being tested
		source_path = os.path.join(get_bench_path(), 'apps', app or 'dataent')
		cov = Coverage(source=[source_path], omit=['*.html', '*.js', '*.css'])
		cov.start()

	ret = dataent.test_runner.main(app, module, doctype, context.verbose, tests=tests,
		force=context.force, profile=profile, junit_xml_output=junit_xml_output,
		ui_tests = ui_tests, doctype_list_path = doctype_list_path, failfast=failfast)

	if coverage:
		cov.stop()
		cov.save()

	if len(ret.failures) == 0 and len(ret.errors) == 0:
		ret = 0

	if os.environ.get('CI'):
		sys.exit(ret)

@click.command('run-ui-tests')
@click.option('--app', help="App to run tests on, leave blank for all apps")
@click.option('--test', help="Path to the specific test you want to run")
@click.option('--test-list', help="Path to the txt file with the list of test cases")
@click.option('--profile', is_flag=True, default=False)
@pass_context
def run_ui_tests(context, app=None, test=False, test_list=False, profile=False):
	"Run UI tests"
	import dataent.test_runner

	site = get_site(context)
	dataent.init(site=site)
	dataent.connect()

	ret = dataent.test_runner.run_ui_tests(app=app, test=test, test_list=test_list, verbose=context.verbose,
		profile=profile)
	if len(ret.failures) == 0 and len(ret.errors) == 0:
		ret = 0

	if os.environ.get('CI'):
		sys.exit(ret)

@click.command('run-setup-wizard-ui-test')
@click.option('--app', help="App to run tests on, leave blank for all apps")
@click.option('--profile', is_flag=True, default=False)
@pass_context
def run_setup_wizard_ui_test(context, app=None, profile=False):
	"Run setup wizard UI test"
	import dataent.test_runner

	site = get_site(context)
	dataent.init(site=site)
	dataent.connect()

	ret = dataent.test_runner.run_setup_wizard_ui_test(app=app, verbose=context.verbose,
		profile=profile)
	if len(ret.failures) == 0 and len(ret.errors) == 0:
		ret = 0

	if os.environ.get('CI'):
		sys.exit(ret)

@click.command('serve')
@click.option('--port', default=8000)
@click.option('--profile', is_flag=True, default=False)
@click.option('--noreload', "no_reload", is_flag=True, default=False)
@click.option('--nothreading', "no_threading", is_flag=True, default=False)
@pass_context
def serve(context, port=None, profile=False, no_reload=False, no_threading=False, sites_path='.', site=None):
	"Start development web server"
	import dataent.app

	if not context.sites:
		site = None
	else:
		site = context.sites[0]

	dataent.app.serve(port=port, profile=profile, no_reload=no_reload, no_threading=no_threading, site=site, sites_path='.')

@click.command('request')
@click.option('--args', help='arguments like `?cmd=test&key=value` or `/api/request/method?..`')
@click.option('--path', help='path to request JSON')
@pass_context
def request(context, args=None, path=None):
	"Run a request as an admin"
	import dataent.handler
	import dataent.api
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			if args:
				if "?" in args:
					dataent.local.form_dict = dataent._dict([a.split("=") for a in args.split("?")[-1].split("&")])
				else:
					dataent.local.form_dict = dataent._dict()

				if args.startswith("/api/method"):
					dataent.local.form_dict.cmd = args.split("?")[0].split("/")[-1]
			elif path:
				with open(os.path.join('..', path), 'r') as f:
					args = json.loads(f.read())

				dataent.local.form_dict = dataent._dict(args)

			dataent.handler.execute_cmd(dataent.form_dict.cmd)

			print(dataent.response)
		finally:
			dataent.destroy()

@click.command('make-app')
@click.argument('destination')
@click.argument('app_name')
def make_app(destination, app_name):
	"Creates a boilerplate app"
	from dataent.utils.boilerplate import make_boilerplate
	make_boilerplate(destination, app_name)

@click.command('set-config')
@click.argument('key')
@click.argument('value')
@click.option('-g', '--global', 'global_', is_flag = True, default = False, help = 'Set Global Site Config')
@click.option('--as-dict', is_flag=True, default=False)
@pass_context
def set_config(context, key, value, global_ = False, as_dict=False):
	"Insert/Update a value in site_config.json"
	from dataent.installer import update_site_config
	import ast
	if as_dict:
		value = ast.literal_eval(value)

	if global_:
		sites_path = os.getcwd() # big assumption.
		common_site_config_path = os.path.join(sites_path, 'common_site_config.json')
		update_site_config(key, value, validate = False, site_config_path = common_site_config_path)
	else:
		for site in context.sites:
			dataent.init(site=site)
			update_site_config(key, value, validate=False)
			dataent.destroy()

@click.command('version')
def get_version():
	"Show the versions of all the installed apps"
	from dataent.utils.change_log import get_app_branch
	dataent.init('')

	for m in sorted(dataent.get_all_apps()):
		branch_name = get_app_branch(m)
		module = dataent.get_module(m)
		app_hooks = dataent.get_module(m + ".hooks")

		if hasattr(app_hooks, '{0}_version'.format(branch_name)):
			print("{0} {1}".format(m, getattr(app_hooks, '{0}_version'.format(branch_name))))

		elif hasattr(module, "__version__"):
			print("{0} {1}".format(m, module.__version__))


@click.command('setup-global-help')
@click.option('--mariadb_root_password')
def setup_global_help(mariadb_root_password=None):
	'''Deprecated: setup help table in a separate database that will be
	shared by the whole bench and set `global_help_setup` as 1 in
	common_site_config.json'''
	print_in_app_help_deprecation()

@click.command('get-docs-app')
@click.argument('app')
def get_docs_app(app):
	'''Deprecated: Get the docs app for given app'''
	print_in_app_help_deprecation()

@click.command('get-all-docs-apps')
def get_all_docs_apps():
	'''Deprecated: Get docs apps for all apps'''
	print_in_app_help_deprecation()

@click.command('setup-help')
@pass_context
def setup_help(context):
	'''Deprecated: Setup help table in the current site (called after migrate)'''
	print_in_app_help_deprecation()

@click.command('rebuild-global-search')
@pass_context
def rebuild_global_search(context):
	'''Setup help table in the current site (called after migrate)'''
	from dataent.utils.global_search import (get_doctypes_with_global_search, rebuild_for_doctype)

	for site in context.sites:
		try:
			dataent.init(site)
			dataent.connect()
			doctypes = get_doctypes_with_global_search()
			for i, doctype in enumerate(doctypes):
				rebuild_for_doctype(doctype)
				update_progress_bar('Rebuilding Global Search', i, len(doctypes))

		finally:
			dataent.destroy()

@click.command('auto-deploy')
@click.argument('app')
@click.option('--migrate', is_flag=True, default=False, help='Migrate after pulling')
@click.option('--restart', is_flag=True, default=False, help='Restart after migration')
@click.option('--remote', default='upstream', help='Remote, default is "upstream"')
@pass_context
def auto_deploy(context, app, migrate=False, restart=False, remote='upstream'):
	'''Pull and migrate sites that have new version'''
	from dataent.utils.gitutils import get_app_branch
	from dataent.utils import get_sites

	branch = get_app_branch(app)
	app_path = dataent.get_app_path(app)

	# fetch
	subprocess.check_output(['git', 'fetch', remote, branch], cwd = app_path)

	# get diff
	if subprocess.check_output(['git', 'diff', '{0}..upstream/{0}'.format(branch)], cwd = app_path):
		print('Updates found for {0}'.format(app))
		if app=='dataent':
			# run bench update
			subprocess.check_output(['bench', 'update', '--no-backup'], cwd = '..')
		else:
			updated = False
			subprocess.check_output(['git', 'pull', '--rebase', 'upstream', branch],
				cwd = app_path)
			# find all sites with that app
			for site in get_sites():
				dataent.init(site)
				if app in dataent.get_installed_apps():
					print('Updating {0}'.format(site))
					updated = True
					subprocess.check_output(['bench', '--site', site, 'clear-cache'], cwd = '..')
					if migrate:
						subprocess.check_output(['bench', '--site', site, 'migrate'], cwd = '..')
				dataent.destroy()

			if updated and restart:
				subprocess.check_output(['bench', 'restart'], cwd = '..')
	else:
		print('No Updates')

def print_in_app_help_deprecation():
	print("In app help has been removed.\nYou can access the documentation on epaas.xyz/docs or epaas.xyz/docs")
	return

commands = [
	build,
	clear_cache,
	clear_website_cache,
	jupyter,
	console,
	destroy_all_sessions,
	execute,
	export_csv,
	export_doc,
	export_fixtures,
	export_json,
	get_version,
	import_csv,
	import_doc,
	make_app,
	mysql,
	mariadb,
	request,
	reset_perms,
	run_tests,
	run_ui_tests,
	run_setup_wizard_ui_test,
	serve,
	set_config,
	watch,
	_bulk_rename,
	add_to_email_queue,
	setup_global_help,
	setup_help,
	rebuild_global_search
]
