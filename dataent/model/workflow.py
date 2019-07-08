# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.utils import cint
from dataent import _

class WorkflowStateError(dataent.ValidationError): pass
class WorkflowTransitionError(dataent.ValidationError): pass
class WorkflowPermissionError(dataent.ValidationError): pass

def get_workflow_name(doctype):
	workflow_name = dataent.cache().hget('workflow', doctype)
	if workflow_name is None:
		workflow_name = dataent.db.get_value("Workflow", {"document_type": doctype,
			"is_active": 1}, "name")
		dataent.cache().hset('workflow', doctype, workflow_name or '')

	return workflow_name

@dataent.whitelist()
def get_transitions(doc, workflow = None):
	'''Return list of possible transitions for the given doc'''
	doc = dataent.get_doc(dataent.parse_json(doc))

	if doc.is_new():
		return []

	dataent.has_permission(doc, 'read', throw=True)
	roles = dataent.get_roles()

	if not workflow:
		workflow = get_workflow(doc.doctype)
	current_state = doc.get(workflow.workflow_state_field)

	if not current_state:
		dataent.throw(_('Workflow State not set'), WorkflowStateError)

	transitions = []
	for transition in workflow.transitions:
		if transition.state == current_state and transition.allowed in roles:
			if transition.condition:
				# if condition, evaluate
				# access to dataent.db.get_value and dataent.db.get_list
				success = dataent.safe_eval(transition.condition,
					dict(dataent = dataent._dict(
						db = dataent._dict(get_value = dataent.db.get_value, get_list=dataent.db.get_list),
						session = dataent.session
					)),
					dict(doc = doc))
				if not success:
					continue
			transitions.append(transition.as_dict())

	return transitions

@dataent.whitelist()
def apply_workflow(doc, action):
	'''Allow workflow action on the current doc'''
	doc = dataent.get_doc(dataent.parse_json(doc))
	workflow = get_workflow(doc.doctype)
	transitions = get_transitions(doc, workflow)
	user = dataent.session.user

	# find the transition
	transition = None
	for t in transitions:
		if t.action == action:
			transition = t

	if not transition:
		dataent.throw(_("Not a valid Workflow Action"), WorkflowTransitionError)

	if not has_approval_access(user, doc, transition):
		dataent.throw(_("Self approval is not allowed"))

	# update workflow state field
	doc.set(workflow.workflow_state_field, transition.next_state)

	# find settings for the next state
	next_state = [d for d in workflow.states if d.state == transition.next_state][0]

	# update any additional field
	if next_state.update_field:
		doc.set(next_state.update_field, next_state.update_value)

	new_docstatus = cint(next_state.doc_status)
	if doc.docstatus == 0 and new_docstatus == 0:
		doc.save()
	elif doc.docstatus == 0 and new_docstatus == 1:
		doc.submit()
	elif doc.docstatus == 1 and new_docstatus == 1:
		doc.save()
	elif doc.docstatus == 1 and new_docstatus == 2:
		doc.cancel()
	else:
		dataent.throw(_('Illegal Document Status for {0}').format(next_state.state))

	doc.add_comment('Workflow', _(next_state.state))

	return doc

def validate_workflow(doc):
	'''Validate Workflow State and Transition for the current user.

	- Check if user is allowed to edit in current state
	- Check if user is allowed to transition to the next state (if changed)
	'''
	workflow = get_workflow(doc.doctype)

	current_state = None
	if getattr(doc, '_doc_before_save', None):
		current_state = doc._doc_before_save.get(workflow.workflow_state_field)
	next_state = doc.get(workflow.workflow_state_field)

	if not next_state:
		next_state = workflow.states[0].state
		doc.set(workflow.workflow_state_field, next_state)

	if not current_state:
		current_state = workflow.states[0].state

	state_row = [d for d in workflow.states if d.state == current_state]
	if not state_row:
		dataent.throw(_('{0} is not a valid Workflow State. Please update your Workflow and try again.'.format(dataent.bold(current_state))))
	state_row = state_row[0]

	# if transitioning, check if user is allowed to transition
	if current_state != next_state:
		bold_current = dataent.bold(current_state)
		bold_next = dataent.bold(next_state)

		if not doc._doc_before_save:
			# transitioning directly to a state other than the first
			# e.g from data import
			dataent.throw(_('Workflow State transition not allowed from {0} to {1}').format(bold_current, bold_next),
				WorkflowPermissionError)

		transitions = get_transitions(doc._doc_before_save)
		transition = [d for d in transitions if d.next_state == next_state]
		if not transition:
			dataent.throw(_('Workflow State transition not allowed from {0} to {1}').format(bold_current, bold_next),
				WorkflowPermissionError)

def get_workflow(doctype):
	return dataent.get_doc('Workflow', get_workflow_name(doctype))

def has_approval_access(user, doc, transition):
	return (user == 'Administrator'
		or transition.get('allow_self_approval')
		or user != doc.owner)

def get_workflow_state_field(workflow_name):
	return get_workflow_field_value(workflow_name, 'workflow_state_field')

def send_email_alert(workflow_name):
	return get_workflow_field_value(workflow_name, 'send_email_alert')

def get_workflow_field_value(workflow_name, field):
	value = dataent.cache().hget('workflow_' + workflow_name, field)
	if value is None:
		value = dataent.db.get_value("Workflow", workflow_name, field)
		dataent.cache().hset('workflow_' + workflow_name, field, value)
	return value