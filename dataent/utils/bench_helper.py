from __future__ import unicode_literals, print_function
import click
import dataent
import os
import json
import importlib
import dataent.utils
import traceback

click.disable_unicode_literals_warning = True

def main():
	commands = get_app_groups()
	commands.update({
		'get-dataent-commands': get_dataent_commands,
		'get-dataent-help': get_dataent_help
	})
	click.Group(commands=commands)(prog_name='bench')

def get_app_groups():
	'''Get all app groups, put them in main group "dataent" since bench is
	designed to only handle that'''
	commands = dict()
	for app in get_apps():
		app_commands = get_app_commands(app)
		if app_commands:
			commands.update(app_commands)

	ret = dict(dataent=click.group(name='dataent', commands=commands)(app_group))
	return ret

def get_app_group(app):
	app_commands = get_app_commands(app)
	if app_commands:
		return click.group(name=app, commands=app_commands)(app_group)

@click.option('--site')
@click.option('--profile', is_flag=True, default=False, help='Profile')
@click.option('--verbose', is_flag=True, default=False, help='Verbose')
@click.option('--force', is_flag=True, default=False, help='Force')
@click.pass_context
def app_group(ctx, site=False, force=False, verbose=False, profile=False):
	ctx.obj = {
		'sites': get_sites(site),
		'force': force,
		'verbose': verbose,
		'profile': profile
	}
	if ctx.info_name == 'dataent':
		ctx.info_name = ''

def get_sites(site_arg):
	if site_arg and site_arg == 'all':
		return dataent.utils.get_sites()
	else:
		if site_arg:
			return [site_arg]
		if os.path.exists('currentsite.txt'):
			with open('currentsite.txt') as f:
				return [f.read().strip()]

def get_app_commands(app):
	if os.path.exists(os.path.join('..', 'apps', app, app, 'commands.py'))\
		or os.path.exists(os.path.join('..', 'apps', app, app, 'commands', '__init__.py')):
		try:
			app_command_module = importlib.import_module(app + '.commands')
		except Exception:
			traceback.print_exc()
			return []
	else:
		return []

	ret = {}
	for command in getattr(app_command_module, 'commands', []):
		ret[command.name] = command
	return ret

@click.command('get-dataent-commands')
def get_dataent_commands():
	commands = list(get_app_commands('dataent'))

	for app in get_apps():
		app_commands = get_app_commands(app)
		if app_commands:
			commands.extend(list(app_commands))

	print(json.dumps(commands))

@click.command('get-dataent-help')
def get_dataent_help():
	print(click.Context(get_app_groups()['dataent']).get_help())

def get_apps():
	return dataent.get_all_apps(with_internal_apps=False, sites_path='.')

if __name__ == "__main__":
	main()

