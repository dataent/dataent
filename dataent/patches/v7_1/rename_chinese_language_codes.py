from __future__ import unicode_literals
import dataent

def execute():
	dataent.rename_doc('Language', 'zh-cn', 'zh', force=True,
		merge=True if dataent.db.exists('Language', 'zh') else False)
	if dataent.db.get_value('Language', 'zh-tw') == 'zh-tw':
		dataent.rename_doc('Language', 'zh-tw', 'zh-TW', force=True)

	dataent.db.set_value('Language', 'zh', 'language_code', 'zh')
	dataent.db.set_value('Language', 'zh-TW', 'language_code', 'zh-TW')