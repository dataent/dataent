from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.model.rename_doc import get_link_fields
from dataent.model.dynamic_links import dynamic_link_queries
from dataent.permissions import reset_perms

def execute():
	dataent.reload_doctype("DocType")
	dataent.reload_doctype("Communication")
	reset_perms("Communication")

	migrate_comments()
	dataent.delete_doc("DocType", "Comment")
	# dataent.db.sql_ddl("drop table `tabComment`")

	migrate_feed()
	dataent.delete_doc("DocType", "Feed")
	# dataent.db.sql_ddl("drop table `tabFeed`")

	update_timeline_doc_for("Blogger")

def migrate_comments():
	from_fields = ""
	to_fields = ""

	if "reference_doctype" in dataent.db.get_table_columns("Comment"):
		from_fields = "reference_doctype as link_doctype, reference_name as link_name,"
		to_fields = "link_doctype, link_name,"

	# comments
	dataent.db.sql("""insert ignore into `tabCommunication` (
			subject,
			content,
			sender,
			sender_full_name,
			comment_type,
			communication_date,
			reference_doctype,
			reference_name,
			{to_fields}

			name,
			user,
			owner,
			creation,
			modified_by,
			modified,
			status,
			sent_or_received,
			communication_type,
			seen
		)
		select
			substring(comment, 1, 100) as subject,
			comment as content,
			comment_by as sender,
			comment_by_fullname as sender_full_name,
			comment_type,
			ifnull(timestamp(comment_date, comment_time), creation) as communication_date,
			comment_doctype as reference_doctype,
			comment_docname as reference_name,
			{from_fields}

			name,
			owner as user,
			owner,
			creation,
			modified_by,
			modified,
			'Linked' as status,
			'Sent' as sent_or_received,
			'Comment' as communication_type,
			1 as seen
		from `tabComment` where comment_doctype is not null and comment_doctype not in ('Message', 'My Company')"""
			.format(to_fields=to_fields, from_fields=from_fields))

	# chat and assignment notifications
	dataent.db.sql("""insert ignore into `tabCommunication` (
			subject,
			content,
			sender,
			sender_full_name,
			comment_type,
			communication_date,
			reference_doctype,
			reference_name,
			{to_fields}

			name,
			user,
			owner,
			creation,
			modified_by,
			modified,
			status,
			sent_or_received,
			communication_type,
			seen
		)
		select
			case
				when parenttype='Assignment' then %(assignment)s
				else substring(comment, 1, 100)
				end
				as subject,
			comment as content,
			comment_by as sender,
			comment_by_fullname as sender_full_name,
			comment_type,
			ifnull(timestamp(comment_date, comment_time), creation) as communication_date,
			'User' as reference_doctype,
			comment_docname as reference_name,
			{from_fields}

			name,
			owner as user,
			owner,
			creation,
			modified_by,
			modified,
			'Linked' as status,
			'Sent' as sent_or_received,
			case
				when parenttype='Assignment' then 'Notification'
				else 'Chat'
				end
				as communication_type,
			1 as seen
		from `tabComment` where comment_doctype in ('Message', 'My Company')"""
			.format(to_fields=to_fields, from_fields=from_fields), {"assignment": _("Assignment")})

def migrate_feed():
	# migrate delete feed
	for doctype in dataent.db.sql("""select distinct doc_type from `tabFeed` where subject=%(deleted)s""", {"deleted": _("Deleted")}):
		dataent.db.sql("""insert ignore into `tabCommunication` (
				subject,
				sender,
				sender_full_name,
				comment_type,
				communication_date,
				reference_doctype,

				name,
				user,
				owner,
				creation,
				modified_by,
				modified,
				status,
				sent_or_received,
				communication_type,
				seen
			)
			select
				concat_ws(" ", %(_doctype)s, doc_name) as subject,
				owner as sender,
				full_name as sender_full_name,
				'Deleted' as comment_type,
				creation as communication_date,
				doc_type as reference_doctype,

				name,
				owner as user,
				owner,
				creation,
				modified_by,
				modified,
				'Linked' as status,
				'Sent' as sent_or_received,
				'Comment' as communication_type,
				1 as seen
			from `tabFeed` where subject=%(deleted)s and doc_type=%(doctype)s""", {
				"deleted": _("Deleted"),
				"doctype": doctype,
				"_doctype": _(doctype)
			})

	# migrate feed type login or empty
	dataent.db.sql("""insert ignore into `tabCommunication` (
			subject,
			sender,
			sender_full_name,
			comment_type,
			communication_date,
			reference_doctype,
			reference_name,

			name,
			user,
			owner,
			creation,
			modified_by,
			modified,
			status,
			sent_or_received,
			communication_type,
			seen
		)
		select
			subject,
			owner as sender,
			full_name as sender_full_name,
			case
				when feed_type='Login' then 'Info'
				else 'Updated'
				end as comment_type,
			creation as communication_date,
			doc_type as reference_doctype,
			doc_name as reference_name,

			name,
			owner as user,
			owner,
			creation,
			modified_by,
			modified,
			'Linked' as status,
			'Sent' as sent_or_received,
			'Comment' as communication_type,
			1 as seen
		from `tabFeed` where (feed_type in ('Login', '') or feed_type is null)""")

def update_timeline_doc_for(timeline_doctype):
	"""NOTE: This method may be used by other apps for patching. It also has COMMIT after each update."""

	# find linked doctypes
	# link fields
	update_for_linked_docs(timeline_doctype)

	# dynamic link fields
	update_for_dynamically_linked_docs(timeline_doctype)

def update_for_linked_docs(timeline_doctype):
	for df in get_link_fields(timeline_doctype):
		if df.issingle:
			continue

		reference_doctype = df.parent

		if not is_valid_timeline_doctype(reference_doctype, timeline_doctype):
			continue

		for doc in dataent.get_all(reference_doctype, fields=["name", df.fieldname]):
			timeline_name = doc.get(df.fieldname)
			update_communication(timeline_doctype, timeline_name, reference_doctype, doc.name)

def update_for_dynamically_linked_docs(timeline_doctype):
	dynamic_link_fields = []
	for query in dynamic_link_queries:
		for df in dataent.db.sql(query, as_dict=True):
			dynamic_link_fields.append(df)

	for df in dynamic_link_fields:
		reference_doctype = df.parent

		if not is_valid_timeline_doctype(reference_doctype, timeline_doctype):
			continue

		try:
			docs = dataent.get_all(reference_doctype, fields=["name", df.fieldname],
				filters={ df.options: timeline_doctype })
		except dataent.SQLError as e:
			if e.args and e.args[0]==1146:
				# single
				continue
			else:
				raise

		for doc in docs:
			timeline_name = doc.get(df.fieldname)
			update_communication(timeline_doctype, timeline_name, reference_doctype, doc.name)

def update_communication(timeline_doctype, timeline_name, reference_doctype, reference_name):
	if not timeline_name:
		return

	dataent.db.sql("""update `tabCommunication` set timeline_doctype=%(timeline_doctype)s, timeline_name=%(timeline_name)s
		where (reference_doctype=%(reference_doctype)s and reference_name=%(reference_name)s)
			and (timeline_doctype is null or timeline_doctype='')
			and (timeline_name is null or timeline_name='')""", {
				"timeline_doctype": timeline_doctype,
				"timeline_name": timeline_name,
				"reference_doctype": reference_doctype,
				"reference_name": reference_name
			})

	dataent.db.commit()

def is_valid_timeline_doctype(reference_doctype, timeline_doctype):
	# for reloading timeline_field
	dataent.reload_doctype(reference_doctype)

	# make sure the timeline field's doctype is same as timeline doctype
	meta = dataent.get_meta(reference_doctype)
	if not meta.timeline_field:
		return False

	doctype = meta.get_link_doctype(meta.timeline_field)
	if doctype != timeline_doctype:
		return False


	return True
