from __future__ import unicode_literals
import dataent
from dataent.translate import get_lang_dict

def execute():
	dataent.reload_doc('core', 'doctype', 'language')

	from dataent.core.doctype.language.language import sync_languages
	sync_languages()

	# move language from old style to new style for old accounts
	# i.e. from "english" to "en"

	lang_dict = get_lang_dict()
	language = dataent.db.get_value('System Settings', None, 'language')
	if language:
		dataent.db.set_value('System Settings', None, 'language', lang_dict.get('language') or 'en')

	for user in dataent.get_all('User', fields=['name', 'language']):
		if user.language:
			dataent.db.set_value('User', user.name, 'language',
				lang_dict.get('language') or 'en', update_modified=False)
