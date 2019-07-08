# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import dataent
import dataent.model.meta
from dataent.model.dynamic_links import get_dynamic_link_map
import dataent.defaults
from dataent.utils.file_manager import remove_all
from dataent.utils.password import delete_all_passwords_for
from dataent import _
from dataent.model.naming import revert_series_if_last
from dataent.utils.global_search import delete_for_document
from six import string_types, integer_types

def delete_doc(doctype=None, name=None, force=0, ignore_doctypes=None, for_reload=False,
	ignore_permissions=False, flags=None, ignore_on_trash=False, ignore_missing=True):
	"""
		Deletes a doc(dt, dn) and validates if it is not submitted and not linked in a live record
	"""
	if not ignore_doctypes: ignore_doctypes = []

	# get from form
	if not doctype:
		doctype = dataent.form_dict.get('dt')
		name = dataent.form_dict.get('dn')

	names = name
	if isinstance(name, string_types) or isinstance(name, integer_types):
		names = [name]

	for name in names or []:

		# already deleted..?
		if not dataent.db.exists(doctype, name):
			if not ignore_missing:
				raise dataent.DoesNotExistError
			else:
				return False

		# delete passwords
		delete_all_passwords_for(doctype, name)

		doc = None
		if doctype=="DocType":
			if for_reload:

				try:
					doc = dataent.get_doc(doctype, name)
				except dataent.DoesNotExistError:
					pass
				else:
					doc.run_method("before_reload")

			else:
				doc = dataent.get_doc(doctype, name)

				update_flags(doc, flags, ignore_permissions)
				check_permission_and_not_submitted(doc)

				dataent.db.sql("delete from `tabCustom Field` where dt = %s", name)
				dataent.db.sql("delete from `tabCustom Script` where dt = %s", name)
				dataent.db.sql("delete from `tabProperty Setter` where doc_type = %s", name)
				dataent.db.sql("delete from `tabReport` where ref_doctype=%s", name)
				dataent.db.sql("delete from `tabCustom DocPerm` where parent=%s", name)

			delete_from_table(doctype, name, ignore_doctypes, None)

		else:
			doc = dataent.get_doc(doctype, name)

			if not for_reload:
				update_flags(doc, flags, ignore_permissions)
				check_permission_and_not_submitted(doc)

				if not ignore_on_trash:
					doc.run_method("on_trash")
					doc.flags.in_delete = True
					doc.run_method('on_change')

				dataent.enqueue('dataent.model.delete_doc.delete_dynamic_links', doctype=doc.doctype, name=doc.name,
					is_async=False if dataent.flags.in_test else True)

				# check if links exist
				if not force:
					check_if_doc_is_linked(doc)
					check_if_doc_is_dynamically_linked(doc)

			update_naming_series(doc)
			delete_from_table(doctype, name, ignore_doctypes, doc)
			doc.run_method("after_delete")

			# delete attachments
			remove_all(doctype, name, from_delete=True)

		# delete global search entry
		delete_for_document(doc)

		if doc and not for_reload:
			add_to_deleted_document(doc)
			if not dataent.flags.in_patch:
				try:
					doc.notify_update()
					insert_feed(doc)
				except ImportError:
					pass

			# delete user_permissions
			dataent.defaults.clear_default(parenttype="User Permission", key=doctype, value=name)

def add_to_deleted_document(doc):
	'''Add this document to Deleted Document table. Called after delete'''
	if doc.doctype != 'Deleted Document' and dataent.flags.in_install != 'dataent':
		dataent.get_doc(dict(
			doctype='Deleted Document',
			deleted_doctype=doc.doctype,
			deleted_name=doc.name,
			data=doc.as_json(),
			owner=dataent.session.user
		)).db_insert()

def update_naming_series(doc):
	if doc.meta.autoname:
		if doc.meta.autoname.startswith("naming_series:") \
			and getattr(doc, "naming_series", None):
			revert_series_if_last(doc.naming_series, doc.name)

		elif doc.meta.autoname.split(":")[0] not in ("Prompt", "field", "hash"):
			revert_series_if_last(doc.meta.autoname, doc.name)

def delete_from_table(doctype, name, ignore_doctypes, doc):
	if doctype!="DocType" and doctype==name:
		dataent.db.sql("delete from `tabSingles` where doctype=%s", name)
	else:
		dataent.db.sql("delete from `tab{0}` where name=%s".format(doctype), name)

	# get child tables
	if doc:
		tables = [d.options for d in doc.meta.get_table_fields()]

	else:
		def get_table_fields(field_doctype):
			return dataent.db.sql_list("""select options from `tab{}` where fieldtype='Table'
				and parent=%s""".format(field_doctype), doctype)

		tables = get_table_fields("DocField")
		if not dataent.flags.in_install=="dataent":
			tables += get_table_fields("Custom Field")

	# delete from child tables
	for t in list(set(tables)):
		if t not in ignore_doctypes:
			dataent.db.sql("delete from `tab%s` where parenttype=%s and parent = %s" % (t, '%s', '%s'), (doctype, name))

def update_flags(doc, flags=None, ignore_permissions=False):
	if ignore_permissions:
		if not flags: flags = {}
		flags["ignore_permissions"] = ignore_permissions

	if flags:
		doc.flags.update(flags)

def check_permission_and_not_submitted(doc):
	# permission
	if (not doc.flags.ignore_permissions
		and dataent.session.user!="Administrator"
		and (
			not doc.has_permission("delete")
			or (doc.doctype=="DocType" and not doc.custom))):
		dataent.msgprint(_("User not allowed to delete {0}: {1}")
			.format(doc.doctype, doc.name), raise_exception=dataent.PermissionError)

	# check if submitted
	if doc.docstatus == 1:
		dataent.msgprint(_("{0} {1}: Submitted Record cannot be deleted.").format(_(doc.doctype), doc.name),
			raise_exception=True)

def check_if_doc_is_linked(doc, method="Delete"):
	"""
		Raises excption if the given doc(dt, dn) is linked in another record.
	"""
	from dataent.model.rename_doc import get_link_fields
	link_fields = get_link_fields(doc.doctype)
	link_fields = [[lf['parent'], lf['fieldname'], lf['issingle']] for lf in link_fields]

	for link_dt, link_field, issingle in link_fields:
		if not issingle:
			for item in dataent.db.get_values(link_dt, {link_field:doc.name},
				["name", "parent", "parenttype", "docstatus"], as_dict=True):
				linked_doctype = item.parenttype if item.parent else link_dt
				if linked_doctype in ("Communication", "ToDo", "DocShare", "Email Unsubscribe", 'File', 'Version', "Activity Log"):
					# don't check for communication and todo!
					continue

				if not item:
					continue
				elif (method != "Delete" or item.docstatus == 2) and (method != "Cancel" or item.docstatus != 1):
					# don't raise exception if not
					# linked to a non-cancelled doc when deleting or to a submitted doc when cancelling
					continue
				elif link_dt == doc.doctype and (item.parent or item.name) == doc.name:
					# don't raise exception if not
					# linked to same item or doc having same name as the item
					continue
				else:
					reference_docname = item.parent or item.name
					raise_link_exists_exception(doc, linked_doctype, reference_docname)

		else:
			if dataent.db.get_value(link_dt, None, link_field) == doc.name:
				raise_link_exists_exception(doc, link_dt, link_dt)

def check_if_doc_is_dynamically_linked(doc, method="Delete"):
	'''Raise `dataent.LinkExistsError` if the document is dynamically linked'''
	for df in get_dynamic_link_map().get(doc.doctype, []):
		if df.parent in ("Communication", "ToDo", "DocShare", "Email Unsubscribe", "Activity Log", 'File', 'Version', 'View Log'):
			# don't check for communication and todo!
			continue

		meta = dataent.get_meta(df.parent)
		if meta.issingle:
			# dynamic link in single doc
			refdoc = dataent.db.get_singles_dict(df.parent)
			if (refdoc.get(df.options)==doc.doctype
				and refdoc.get(df.fieldname)==doc.name
				and ((method=="Delete" and refdoc.docstatus < 2)
					or (method=="Cancel" and refdoc.docstatus==1))
				):
				# raise exception only if
				# linked to an non-cancelled doc when deleting
				# or linked to a submitted doc when cancelling
				raise_link_exists_exception(doc, df.parent, df.parent)
		else:
			# dynamic link in table
			df["table"] = ", parent, parenttype, idx" if meta.istable else ""
			for refdoc in dataent.db.sql("""select name, docstatus{table} from `tab{parent}` where
				{options}=%s and {fieldname}=%s""".format(**df), (doc.doctype, doc.name), as_dict=True):

				if ((method=="Delete" and refdoc.docstatus < 2) or (method=="Cancel" and refdoc.docstatus==1)):
					# raise exception only if
					# linked to an non-cancelled doc when deleting
					# or linked to a submitted doc when cancelling

					reference_doctype = refdoc.parenttype if meta.istable else df.parent
					reference_docname = refdoc.parent if meta.istable else refdoc.name
					at_position = "at Row: {0}".format(refdoc.idx) if meta.istable else ""

					raise_link_exists_exception(doc, reference_doctype, reference_docname, at_position)

def raise_link_exists_exception(doc, reference_doctype, reference_docname, row=''):
	doc_link = '<a href="#Form/{0}/{1}">{1}</a>'.format(doc.doctype, doc.name)
	reference_link = '<a href="#Form/{0}/{1}">{1}</a>'.format(reference_doctype, reference_docname)

	#hack to display Single doctype only once in message
	if reference_doctype == reference_docname:
		reference_doctype = ''

	dataent.throw(_('Cannot delete or cancel because {0} {1} is linked with {2} {3} {4}')
		.format(doc.doctype, doc_link, reference_doctype, reference_link, row), dataent.LinkExistsError)

def delete_dynamic_links(doctype, name):
	delete_doc("ToDo", dataent.db.sql_list("""select name from `tabToDo`
		where reference_type=%s and reference_name=%s""", (doctype, name)),
		ignore_permissions=True, force=True)

	dataent.db.sql('''delete from `tabEmail Unsubscribe`
		where reference_doctype=%s and reference_name=%s''', (doctype, name))

	# delete shares
	dataent.db.sql("""delete from `tabDocShare`
		where share_doctype=%s and share_name=%s""", (doctype, name))

	# delete versions
	dataent.db.sql('delete from tabVersion where ref_doctype=%s and docname=%s', (doctype, name))

	# delete comments
	dataent.db.sql("""delete from `tabCommunication`
		where
			communication_type = 'Comment'
			and reference_doctype=%s and reference_name=%s""", (doctype, name))

	# delete view logs
	dataent.db.sql("""delete from `tabView Log`
		where reference_doctype=%s and reference_name=%s""", (doctype, name))

	# unlink communications
	dataent.db.sql("""update `tabCommunication`
		set reference_doctype=null, reference_name=null
		where
			communication_type = 'Communication'
			and reference_doctype=%s
			and reference_name=%s""", (doctype, name))

	# unlink secondary references
	dataent.db.sql("""update `tabCommunication`
		set link_doctype=null, link_name=null
		where link_doctype=%s and link_name=%s""", (doctype, name))

	# unlink feed
	dataent.db.sql("""update `tabCommunication`
		set timeline_doctype=null, timeline_name=null
		where timeline_doctype=%s and timeline_name=%s""", (doctype, name))

	# unlink activity_log reference_doctype
	dataent.db.sql("""update `tabActivity Log`
		set reference_doctype=null, reference_name=null
		where
			reference_doctype=%s
			and reference_name=%s""", (doctype, name))

	# unlink activity_log timeline_doctype
	dataent.db.sql("""update `tabActivity Log`
		set timeline_doctype=null, timeline_name=null
		where timeline_doctype=%s and timeline_name=%s""", (doctype, name))

def insert_feed(doc):
	from dataent.utils import get_fullname

	if dataent.flags.in_install or dataent.flags.in_import or getattr(doc, "no_feed_on_delete", False):
		return

	dataent.get_doc({
		"doctype": "Communication",
		"communication_type": "Comment",
		"comment_type": "Deleted",
		"reference_doctype": doc.doctype,
		"subject": "{0} {1}".format(_(doc.doctype), doc.name),
		"full_name": get_fullname(doc.owner)
	}).insert(ignore_permissions=True)
