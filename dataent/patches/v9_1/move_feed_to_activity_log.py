from __future__ import unicode_literals
import dataent
from dataent.utils.background_jobs import enqueue

def execute():
	comm_records_count = dataent.db.count("Communication", {"comment_type": "Updated"})
	if comm_records_count > 100000:
		enqueue(method=move_data_from_communication_to_activity_log, queue='short', now=True)
	else:
		move_data_from_communication_to_activity_log()

def move_data_from_communication_to_activity_log():
	dataent.reload_doc("core", "doctype", "communication")
	dataent.reload_doc("core", "doctype", "activity_log")

	dataent.db.sql("""insert into `tabActivity Log` (name, owner, modified, creation, status, communication_date,
			reference_doctype, reference_name, timeline_doctype, timeline_name, link_doctype, link_name, subject, content, user)
			select name, owner, modified, creation, status, communication_date,
			reference_doctype, reference_name, timeline_doctype, timeline_name, link_doctype, link_name, subject, content, user
			from `tabCommunication`
			where comment_type = 'Updated'""")

	dataent.db.sql("""delete from `tabCommunication` where comment_type = 'Updated'""")
	dataent.delete_doc("DocType", "Authentication Log")