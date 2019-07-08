# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent, json, re
from dataent import _
from dataent.model.document import Document

class Language(Document):
	def validate(self):
		validate_with_regex(self.language_code, "Language Code")

	def before_rename(self, old, new, merge=False):
		validate_with_regex(new, "Name")

def validate_with_regex(name, label):
	pattern = re.compile("^[a-zA-Z]+[-_]*[a-zA-Z]+$")
	if not pattern.match(name):
		dataent.throw(_("""{0} must begin and end with a letter and can only contain letters,
				hyphen or underscore.""").format(label))

def export_languages_json():
	'''Export list of all languages'''
	languages = dataent.db.get_all('Language', fields=['name', 'language_name'])
	languages = [{'name': d.language_name, 'code': d.name} for d in languages]

	languages.sort(key = lambda a: a['code'])

	with open(dataent.get_app_path('dataent', 'geo', 'languages.json'), 'w') as f:
		f.write(dataent.as_json(languages))

def sync_languages():
	'''Sync dataent/geo/languages.json with Language'''
	with open(dataent.get_app_path('dataent', 'geo', 'languages.json'), 'r') as f:
		data = json.loads(f.read())

	for l in data:
		if not dataent.db.exists('Language', l['code']):
			dataent.get_doc({
				'doctype': 'Language',
				'language_code': l['code'],
				'language_name': l['name']
			}).insert()

def update_language_names():
	'''Update dataent/geo/languages.json names (for use via patch)'''
	with open(dataent.get_app_path('dataent', 'geo', 'languages.json'), 'r') as f:
		data = json.loads(f.read())

	for l in data:
		dataent.db.set_value('Language', l['code'], 'language_name', l['name'])