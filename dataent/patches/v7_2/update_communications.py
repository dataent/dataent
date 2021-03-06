from __future__ import unicode_literals
import dataent

def execute():
	"""
		in communication move feedback details to content
		remove Guest None from sender full name
		setup feedback request trigger's is_manual field
	"""
	dataent.reload_doc('core', 'doctype', 'dynamic_link')
	dataent.reload_doc('email', 'doctype', 'contact')
	
	dataent.reload_doc("core", "doctype", "feedback_request")
	dataent.reload_doc("core", "doctype", "communication")
	
	if dataent.db.has_column('Communication', 'feedback'):
		dataent.db.sql("""update tabCommunication set content=ifnull(feedback, "feedback details not provided")
			where communication_type="Feedback" and content is NULL""")

	dataent.db.sql(""" update tabCommunication set sender_full_name="" where communication_type="Feedback"
		and sender_full_name='Guest None' """)

	dataent.db.sql(""" update `tabFeedback Request` set is_manual=1, feedback_trigger="Manual"
		where ifnull(feedback_trigger, '')='' """)