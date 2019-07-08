from __future__ import unicode_literals
import dataent
from dataent.model.meta import is_single

def execute():
	"""Fix old style file urls that start with files/"""
	fix_file_urls()
	fix_attach_field_urls()

def fix_file_urls():
	for file in dataent.db.sql_list("""select name from `tabFile` where file_url like 'files/%'"""):
		file = dataent.get_doc("File", file)
		file.db_set("file_url", "/" + file.file_url, update_modified=False)
		try:
			file.validate_file()
			file.db_set("file_name", file.file_name, update_modified=False)
			if not file.content_hash:
				file.generate_content_hash()
				file.db_set("content_hash", file.content_hash, update_modified=False)

		except IOError:
			pass

def fix_attach_field_urls():
	# taken from an old patch
	attach_fields = (dataent.db.sql("""select parent, fieldname from `tabDocField` where fieldtype in ('Attach', 'Attach Image')""") +
		dataent.db.sql("""select dt, fieldname from `tabCustom Field` where fieldtype in ('Attach', 'Attach Image')"""))

	for doctype, fieldname in attach_fields:
		if is_single(doctype):
			dataent.db.sql("""update `tabSingles` set value=concat("/", `value`)
				where doctype=%(doctype)s and field=%(fieldname)s
					and value like 'files/%%'""", {"doctype": doctype, "fieldname": fieldname})
		else:
			dataent.db.sql("""update `tab{doctype}` set `{fieldname}`=concat("/", `{fieldname}`)
				where `{fieldname}` like 'files/%'""".format(doctype=doctype, fieldname=fieldname))
