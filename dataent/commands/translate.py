from __future__ import unicode_literals, absolute_import, print_function
import click
from dataent.commands import pass_context, get_site

# translation
@click.command('build-message-files')
@pass_context
def build_message_files(context):
	"Build message files for translation"
	import dataent.translate
	for site in context.sites:
		try:
			dataent.init(site=site)
			dataent.connect()
			dataent.translate.rebuild_all_translation_files()
		finally:
			dataent.destroy()

@click.command('new-language') #, help="Create lang-code.csv for given app")
@pass_context
@click.argument('lang_code') #, help="Language code eg. en")
@click.argument('app') #, help="App name eg. dataent")
def new_language(context, lang_code, app):
	"""Create lang-code.csv for given app"""
	import dataent.translate

	if not context['sites']:
		raise Exception('--site is required')

	# init site
	dataent.connect(site=context['sites'][0])
	dataent.translate.write_translations_file(app, lang_code)

	print("File created at ./apps/{app}/{app}/translations/{lang_code}.csv".format(app=app, lang_code=lang_code))
	print("You will need to add the language in dataent/geo/languages.json, if you haven't done it already.")

@click.command('get-untranslated')
@click.argument('lang')
@click.argument('untranslated_file')
@click.option('--all', default=False, is_flag=True, help='Get all message strings')
@pass_context
def get_untranslated(context, lang, untranslated_file, all=None):
	"Get untranslated strings for language"
	import dataent.translate
	site = get_site(context)
	try:
		dataent.init(site=site)
		dataent.connect()
		dataent.translate.get_untranslated(lang, untranslated_file, get_all=all)
	finally:
		dataent.destroy()

@click.command('update-translations')
@click.argument('lang')
@click.argument('untranslated_file')
@click.argument('translated-file')
@pass_context
def update_translations(context, lang, untranslated_file, translated_file):
	"Update translated strings"
	import dataent.translate
	site = get_site(context)
	try:
		dataent.init(site=site)
		dataent.connect()
		dataent.translate.update_translations(lang, untranslated_file, translated_file)
	finally:
		dataent.destroy()

@click.command('import-translations')
@click.argument('lang')
@click.argument('path')
@pass_context
def import_translations(context, lang, path):
	"Update translated strings"
	import dataent.translate
	site = get_site(context)
	try:
		dataent.init(site=site)
		dataent.connect()
		dataent.translate.import_translations(lang, path)
	finally:
		dataent.destroy()

commands = [
	build_message_files,
	get_untranslated,
	import_translations,
	new_language,
	update_translations,
]
