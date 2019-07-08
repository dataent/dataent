from __future__ import print_function, unicode_literals
import dataent

def execute():
	from dataent.core.doctype.file.file import make_home_folder

	if not dataent.db.exists("DocType", "File"):
		dataent.rename_doc("DocType", "File Data", "File")
		dataent.reload_doctype("File")

	if not dataent.db.exists("File", {"is_home_folder": 1}):
		make_home_folder()

	# make missing folders and set parent folder
	for file in dataent.get_all("File", filters={"is_folder": 0}):
		file = dataent.get_doc("File", file.name)
		file.flags.ignore_folder_validate = True
		file.flags.ignore_file_validate = True
		file.flags.ignore_duplicate_entry_error = True
		file.flags.ignore_links = True
		file.set_folder_name()
		try:
			file.save()
		except:
			print(dataent.get_traceback())
			raise

	from dataent.utils.nestedset import rebuild_tree
	rebuild_tree("File", "folder")

	# reset file size
	for folder in dataent.db.sql("""select name from tabFile f1 where is_folder = 1 and
		(select count(*) from tabFile f2 where f2.folder = f1.name and f2.is_folder = 1) = 0"""):
		folder = dataent.get_doc("File", folder[0])
		folder.save()



