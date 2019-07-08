# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# called from wnf.py
# lib/wnf.py --install [rootpassword] [dbname] [source]

from __future__ import unicode_literals, print_function

from six.moves import input

import os, json, sys, subprocess, shutil
import dataent
import dataent.database
import getpass
import importlib
from dataent import _
from dataent.model.db_schema import DbManager
from dataent.model.sync import sync_for
from dataent.utils.fixtures import sync_fixtures
from dataent.website import render
from dataent.desk.doctype.desktop_icon.desktop_icon import sync_from_app
from dataent.utils.password import create_auth_table
from dataent.utils.global_search import setup_global_search_table
from dataent.modules.utils import sync_customizations

def install_db(root_login="root", root_password=None, db_name=None, source_sql=None,
	admin_password=None, verbose=True, force=0, site_config=None, reinstall=False):
	make_conf(db_name, site_config=site_config)
	dataent.flags.in_install_db = True
	if reinstall:
		dataent.connect(db_name=db_name)
		dbman = DbManager(dataent.local.db)
		dbman.create_database(db_name)

	else:
		dataent.local.db = get_root_connection(root_login, root_password)
		dataent.local.session = dataent._dict({'user':'Administrator'})
		create_database_and_user(force, verbose)

	dataent.conf.admin_password = dataent.conf.admin_password or admin_password

	dataent.connect(db_name=db_name)
	check_if_ready_for_barracuda()
	import_db_from_sql(source_sql, verbose)
	if not 'tabDefaultValue' in dataent.db.get_tables():
		print('''Database not installed, this can due to lack of permission, or that the database name exists.
Check your mysql root password, or use --force to reinstall''')
		sys.exit(1)

	remove_missing_apps()

	create_auth_table()
	setup_global_search_table()
	create_user_settings_table()

	dataent.flags.in_install_db = False


def create_database_and_user(force, verbose):
	db_name = dataent.local.conf.db_name
	dbman = DbManager(dataent.local.db)
	if force or (db_name not in dbman.get_database_list()):
		dbman.delete_user(db_name)
		dbman.drop_database(db_name)
	else:
		raise Exception("Database %s already exists" % (db_name,))

	dbman.create_user(db_name, dataent.conf.db_password)
	if verbose: print("Created user %s" % db_name)

	dbman.create_database(db_name)
	if verbose: print("Created database %s" % db_name)

	dbman.grant_all_privileges(db_name, db_name)
	dbman.flush_privileges()
	if verbose: print("Granted privileges to user %s and database %s" % (db_name, db_name))

	# close root connection
	dataent.db.close()

def create_user_settings_table():
	dataent.db.sql_ddl("""create table if not exists __UserSettings (
		`user` VARCHAR(180) NOT NULL,
		`doctype` VARCHAR(180) NOT NULL,
		`data` TEXT,
		UNIQUE(user, doctype)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8""")

def import_db_from_sql(source_sql, verbose):
	if verbose: print("Starting database import...")
	db_name = dataent.conf.db_name
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(dataent.__file__), 'data', 'Framework.sql')
	DbManager(dataent.local.db).restore_database(db_name, source_sql, db_name, dataent.conf.db_password)
	if verbose: print("Imported from database %s" % source_sql)

def get_root_connection(root_login='root', root_password=None):
	if not dataent.local.flags.root_connection:
		if root_login:
			if not root_password:
				root_password = dataent.conf.get("root_password") or None

			if not root_password:
				root_password = getpass.getpass("MySQL root password: ")
		dataent.local.flags.root_connection = dataent.database.Database(user=root_login, password=root_password)

	return dataent.local.flags.root_connection

def install_app(name, verbose=False, set_as_patched=True):
	dataent.flags.in_install = name
	dataent.flags.ignore_in_install = False

	dataent.clear_cache()
	app_hooks = dataent.get_hooks(app_name=name)
	installed_apps = dataent.get_installed_apps()

	# install pre-requisites
	if app_hooks.required_apps:
		for app in app_hooks.required_apps:
			install_app(app)

	dataent.flags.in_install = name
	dataent.clear_cache()

	if name not in dataent.get_all_apps():
		raise Exception("App not in apps.txt")

	if name in installed_apps:
		dataent.msgprint(_("App {0} already installed").format(name))
		return

	print("\nInstalling {0}...".format(name))

	if name != "dataent":
		dataent.only_for("System Manager")

	for before_install in app_hooks.before_install or []:
		out = dataent.get_attr(before_install)()
		if out==False:
			return

	if name != "dataent":
		add_module_defs(name)

	sync_for(name, force=True, sync_everything=True, verbose=verbose, reset_permissions=True)

	sync_from_app(name)

	add_to_installed_apps(name)

	dataent.get_doc('Portal Settings', 'Portal Settings').sync_menu()

	if set_as_patched:
		set_all_patches_as_completed(name)

	for after_install in app_hooks.after_install or []:
		dataent.get_attr(after_install)()

	sync_fixtures(name)
	sync_customizations(name)

	for after_sync in app_hooks.after_sync or []:
		dataent.get_attr(after_sync)() #

	dataent.flags.in_install = False

def add_to_installed_apps(app_name, rebuild_website=True):
	installed_apps = dataent.get_installed_apps()
	if not app_name in installed_apps:
		installed_apps.append(app_name)
		dataent.db.set_global("installed_apps", json.dumps(installed_apps))
		dataent.db.commit()
		post_install(rebuild_website)

def remove_from_installed_apps(app_name):
	installed_apps = dataent.get_installed_apps()
	if app_name in installed_apps:
		installed_apps.remove(app_name)
		dataent.db.set_global("installed_apps", json.dumps(installed_apps))
		dataent.db.commit()
		if dataent.flags.in_install:
			post_install()

def remove_app(app_name, dry_run=False, yes=False):
	"""Delete app and all linked to the app's module with the app."""

	if not dry_run and not yes:
		confirm = input("All doctypes (including custom), modules related to this app will be deleted. Are you sure you want to continue (y/n) ? ")
		if confirm!="y":
			return

	from dataent.utils.backups import scheduled_backup
	print("Backing up...")
	scheduled_backup(ignore_files=True)

	drop_doctypes = []

	# remove modules, doctypes, roles
	for module_name in dataent.get_module_list(app_name):
		for doctype in dataent.get_list("DocType", filters={"module": module_name},
			fields=["name", "issingle"]):
			print("removing DocType {0}...".format(doctype.name))

			if not dry_run:
				dataent.delete_doc("DocType", doctype.name)

				if not doctype.issingle:
					drop_doctypes.append(doctype.name)

		# remove reports, pages and web forms
		for doctype in ("Report", "Page", "Web Form"):
			for record in dataent.get_list(doctype, filters={"module": module_name}):
				print("removing {0} {1}...".format(doctype, record.name))
				if not dry_run:
					dataent.delete_doc(doctype, record.name)

		print("removing Module {0}...".format(module_name))
		if not dry_run:
			dataent.delete_doc("Module Def", module_name)

	# delete desktop icons
	dataent.db.sql('delete from `tabDesktop Icon` where app=%s', app_name)

	remove_from_installed_apps(app_name)

	if not dry_run:
		# drop tables after a commit
		dataent.db.commit()

		for doctype in set(drop_doctypes):
			dataent.db.sql("drop table `tab{0}`".format(doctype))

def post_install(rebuild_website=False):
	if rebuild_website:
		render.clear_cache()

	init_singles()
	dataent.db.commit()
	dataent.clear_cache()

def set_all_patches_as_completed(app):
	patch_path = os.path.join(dataent.get_pymodule_path(app), "patches.txt")
	if os.path.exists(patch_path):
		for patch in dataent.get_file_items(patch_path):
			dataent.get_doc({
				"doctype": "Patch Log",
				"patch": patch
			}).insert(ignore_permissions=True)
		dataent.db.commit()

def init_singles():
	singles = [single['name'] for single in dataent.get_all("DocType", filters={'issingle': True})]
	for single in singles:
		if not dataent.db.get_singles_dict(single):
			doc = dataent.new_doc(single)
			doc.flags.ignore_mandatory=True
			doc.flags.ignore_validate=True
			doc.save()

def make_conf(db_name=None, db_password=None, site_config=None):
	site = dataent.local.site
	make_site_config(db_name, db_password, site_config)
	sites_path = dataent.local.sites_path
	dataent.destroy()
	dataent.init(site, sites_path=sites_path)

def make_site_config(db_name=None, db_password=None, site_config=None):
	dataent.create_folder(os.path.join(dataent.local.site_path))
	site_file = get_site_config_path()

	if not os.path.exists(site_file):
		if not (site_config and isinstance(site_config, dict)):
			site_config = get_conf_params(db_name, db_password)

		with open(site_file, "w") as f:
			f.write(json.dumps(site_config, indent=1, sort_keys=True))

def update_site_config(key, value, validate=True, site_config_path=None):
	"""Update a value in site_config"""
	if not site_config_path:
		site_config_path = get_site_config_path()

	with open(site_config_path, "r") as f:
		site_config = json.loads(f.read())

	# In case of non-int value
	if value in ('0', '1'):
		value = int(value)

	# boolean
	if value == 'false': value = False
	if value == 'true': value = True

	# remove key if value is None
	if value == "None":
		if key in site_config:
			del site_config[key]
	else:
		site_config[key] = value

	with open(site_config_path, "w") as f:
		f.write(json.dumps(site_config, indent=1, sort_keys=True))
	
	if hasattr(dataent.local, "conf"):
		dataent.local.conf[key] = value

def get_site_config_path():
	return os.path.join(dataent.local.site_path, "site_config.json")

def get_conf_params(db_name=None, db_password=None):
	if not db_name:
		db_name = input("Database Name: ")
		if not db_name:
			raise Exception("Database Name Required")

	if not db_password:
		from dataent.utils import random_string
		db_password = random_string(16)

	return {"db_name": db_name, "db_password": db_password}

def make_site_dirs():
	site_public_path = os.path.join(dataent.local.site_path, 'public')
	site_private_path = os.path.join(dataent.local.site_path, 'private')
	for dir_path in (
			os.path.join(site_private_path, 'backups'),
			os.path.join(site_public_path, 'files'),
			os.path.join(site_private_path, 'files'),
			os.path.join(dataent.local.site_path, 'task-logs')):
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)
	locks_dir = dataent.get_site_path('locks')
	if not os.path.exists(locks_dir):
			os.makedirs(locks_dir)

def add_module_defs(app):
	modules = dataent.get_module_list(app)
	for module in modules:
		d = dataent.new_doc("Module Def")
		d.app_name = app
		d.module_name = module
		d.save(ignore_permissions=True)

def remove_missing_apps():
	apps = ('dataent_subscription', 'shopping_cart')
	installed_apps = json.loads(dataent.db.get_global("installed_apps") or "[]")
	for app in apps:
		if app in installed_apps:
			try:
				importlib.import_module(app)

			except ImportError:
				installed_apps.remove(app)
				dataent.db.set_global("installed_apps", json.dumps(installed_apps))

def check_if_ready_for_barracuda():
	mariadb_variables = dataent._dict(dataent.db.sql("""show variables"""))
	mariadb_minor_version = int(mariadb_variables.get('version').split('-')[0].split('.')[1])
	if mariadb_minor_version < 3:
		check_database(mariadb_variables, {
			"innodb_file_format": "Barracuda",
			"innodb_file_per_table": "ON",
			"innodb_large_prefix": "ON"
		})
	check_database(mariadb_variables, {
		"character_set_server": "utf8mb4",
		"collation_server": "utf8mb4_unicode_ci"
	})

def check_database(mariadb_variables, variables_dict):
	mariadb_minor_version = int(mariadb_variables.get('version').split('-')[0].split('.')[1])
	for key, value in variables_dict.items():
		if mariadb_variables.get(key) != value:
			site = dataent.local.site
			msg = ("Creation of your site - {x} failed because MariaDB is not properly {sep}"
				   "configured to use the Barracuda storage engine. {sep}"
				   "Please add the settings below to MariaDB's my.cnf, restart MariaDB then {sep}"
				   "run `bench new-site {x}` again.{sep2}"
				   "").format(x=site, sep2="\n"*2, sep="\n")

			if mariadb_minor_version < 3:
				print_db_config(msg, expected_config_for_barracuda_2)
			else:
				print_db_config(msg, expected_config_for_barracuda_3)
			raise dataent.exceptions.ImproperDBConfigurationError(
				reason="MariaDB default file format is not Barracuda"
			)


def print_db_config(explanation, config_text):
	print("="*80)
	print(explanation)
	print(config_text)
	print("="*80)


def extract_sql_gzip(sql_gz_path):
	try:
		subprocess.check_call(['gzip', '-d', '-v', '-f', sql_gz_path])
	except:
		raise

	return sql_gz_path[:-3]

def extract_tar_files(site_name, file_path, folder_name):
	# Need to do dataent.init to maintain the site locals
	dataent.init(site=site_name)
	abs_site_path = os.path.abspath(dataent.get_site_path())

	# Copy the files to the parent directory and extract
	shutil.copy2(os.path.abspath(file_path), abs_site_path)

	# Get the file name splitting the file path on
	tar_name = os.path.split(file_path)[1]
	tar_path = os.path.join(abs_site_path, tar_name)

	try:
		subprocess.check_output(['tar', 'xvf', tar_path, '--strip', '2'], cwd=abs_site_path)
	except:
		raise
	finally:
		dataent.destroy()

	return tar_path

expected_config_for_barracuda_2 = """[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
"""

expected_config_for_barracuda_3 = """[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
"""
