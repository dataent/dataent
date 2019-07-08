# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dataent Technologies and Contributors
# See license.txt
from __future__ import unicode_literals
import dataent, unittest

class TestDataMigrationRun(unittest.TestCase):
	def test_run(self):
		create_plan()

		description = 'data migration todo'
		new_todo = dataent.get_doc({
			'doctype': 'ToDo',
			'description': description
		}).insert()

		event_subject = 'data migration event'
		dataent.get_doc(dict(
			doctype='Event',
			subject=event_subject,
			repeat_on='Every Month',
			starts_on=dataent.utils.now_datetime()
		)).insert()

		run = dataent.get_doc({
			'doctype': 'Data Migration Run',
			'data_migration_plan': 'ToDo Sync',
			'data_migration_connector': 'Local Connector'
		}).insert()

		run.run()
		self.assertEqual(run.db_get('status'), 'Success')

		self.assertEqual(run.db_get('push_insert'), 1)
		self.assertEqual(run.db_get('pull_insert'), 1)

		todo = dataent.get_doc('ToDo', new_todo.name)
		self.assertTrue(todo.todo_sync_id)

		# Pushed Event
		event = dataent.get_doc('Event', todo.todo_sync_id)
		self.assertEqual(event.subject, description)

		# Pulled ToDo
		created_todo = dataent.get_doc('ToDo', {'description': event_subject})
		self.assertEqual(created_todo.description, event_subject)

		todo_list = dataent.get_list('ToDo', filters={'description': 'Data migration todo'}, fields=['name'])
		todo_name = todo_list[0].name

		todo = dataent.get_doc('ToDo', todo_name)
		todo.description = 'Data migration todo updated'
		todo.save()

		run = dataent.get_doc({
			'doctype': 'Data Migration Run',
			'data_migration_plan': 'ToDo Sync',
			'data_migration_connector': 'Local Connector'
		}).insert()

		run.run()

		# Update
		self.assertEqual(run.db_get('status'), 'Success')
		self.assertEqual(run.db_get('pull_update'), 1)

def create_plan():
	dataent.get_doc({
		'doctype': 'Data Migration Mapping',
		'mapping_name': 'Todo to Event',
		'remote_objectname': 'Event',
		'remote_primary_key': 'name',
		'mapping_type': 'Push',
		'local_doctype': 'ToDo',
		'fields': [
			{ 'remote_fieldname': 'subject', 'local_fieldname': 'description' },
			{ 'remote_fieldname': 'starts_on', 'local_fieldname': 'eval:dataent.utils.get_datetime_str(dataent.utils.get_datetime())' }
		],
		'condition': '{"description": "data migration todo" }'
	}).insert()

	dataent.get_doc({
		'doctype': 'Data Migration Mapping',
		'mapping_name': 'Event to ToDo',
		'remote_objectname': 'Event',
		'remote_primary_key': 'name',
		'local_doctype': 'ToDo',
		'local_primary_key': 'name',
		'mapping_type': 'Pull',
		'condition': '{"subject": "data migration event" }',
		'fields': [
			{ 'remote_fieldname': 'subject', 'local_fieldname': 'description' }
		]
	}).insert()

	dataent.get_doc({
		'doctype': 'Data Migration Plan',
		'plan_name': 'ToDo sync',
		'module': 'Core',
		'mappings': [
			{ 'mapping': 'Todo to Event' },
			{ 'mapping': 'Event to ToDo' }
		]
	}).insert()

	dataent.get_doc({
		'doctype': 'Data Migration Connector',
		'connector_name': 'Local Connector',
		'connector_type': 'Dataent',
		'hostname': 'http://localhost:8000',
		'username': 'Administrator',
		'password': 'admin'
	}).insert()
