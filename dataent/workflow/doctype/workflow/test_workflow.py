# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import dataent
import unittest
from dataent.utils import random_string
from dataent.model.workflow import apply_workflow, WorkflowTransitionError, WorkflowPermissionError

class TestWorkflow(unittest.TestCase):
	def setUp(self):
		if not getattr(self, 'workflow', None):
			dataent.get_doc(dict(doctype='Role',
				role_name='Test Approver')).insert(ignore_if_duplicate=True)

			if dataent.db.exists('Workflow', 'Test ToDo'):
				self.workflow = dataent.get_doc('Workflow', 'Test ToDo')
				self.workflow.save()
			else:
				self.workflow = dataent.new_doc('Workflow')
				self.workflow.workflow_name = 'Test ToDo'
				self.workflow.document_type = 'ToDo'
				self.workflow.workflow_state_field = 'workflow_state'
				self.workflow.is_active = 1
				self.workflow.send_email_alert = 0
				self.workflow.append('states', dict(
					state = 'Pending', allow_edit = 'All'
				))
				self.workflow.append('states', dict(
					state = 'Approved', allow_edit = 'Test Approver',
					update_field = 'status', update_value = 'Closed'
				))
				self.workflow.append('states', dict(
					state = 'Rejected', allow_edit = 'Test Approver'
				))
				self.workflow.append('transitions', dict(
					state = 'Pending', action='Approve', next_state = 'Approved', allowed='Test Approver', allow_self_approval= 1
				))
				self.workflow.append('transitions', dict(
					state = 'Pending', action='Reject', next_state = 'Rejected', allowed='Test Approver', allow_self_approval= 1
				))
				self.workflow.append('transitions', dict(
					state = 'Rejected', action='Review', next_state = 'Pending', allowed='All', allow_self_approval= 1
				))
				self.workflow.insert()
		dataent.set_user('Administrator')

	def test_default_condition(self):
		'''test default condition is set'''
		todo = dataent.get_doc(dict(doctype='ToDo', description='workflow ' + random_string(10))).insert()

		# default condition is set
		self.assertEqual(todo.workflow_state, 'Pending')

		return todo

	def test_approve(self, doc=None):
		'''test simple workflow'''
		todo = doc or self.test_default_condition()

		apply_workflow(todo, 'Approve')
		# default condition is set
		self.assertEqual(todo.workflow_state, 'Approved')
		self.assertEqual(todo.status, 'Closed')

		return todo

	def test_wrong_action(self):
		'''Check illegal action (approve after reject)'''
		todo = self.test_approve()

		self.assertRaises(WorkflowTransitionError, apply_workflow, todo, 'Reject')

	def test_workflow_condition(self):
		'''Test condition in transition'''
		self.workflow.transitions[0].condition = 'doc.status == "Closed"'
		self.workflow.save()

		# only approve if status is closed
		self.assertRaises(WorkflowTransitionError, self.test_approve)

		self.workflow.transitions[0].condition = ''
		self.workflow.save()

	def test_if_workflow_actions_were_processed(self):
		dataent.db.sql('delete from `tabWorkflow Action`')
		user = dataent.get_doc('User', 'test2@example.com')
		user.add_roles('Test Approver', 'System Manager')
		dataent.set_user('test2@example.com')

		doc = self.test_default_condition()
		workflow_actions = dataent.get_all('Workflow Action', fields=['status'])
		self.assertEqual(len(workflow_actions), 1)

		# test if status of workflow actions are updated on approval
		self.test_approve(doc)
		user.remove_roles('Test Approver', 'System Manager')
		workflow_actions = dataent.get_all('Workflow Action', fields=['status'])
		self.assertEqual(len(workflow_actions), 1)
		self.assertEqual(workflow_actions[0].status, 'Completed')
		dataent.set_user('Administrator')
