# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import dataent
from dataent.utils import cint

@dataent.whitelist()
def get_user_progress_slides():
	'''
		Return user progress slides for the desktop (called via `get_user_progress_slides` hook)
	'''
	slides = []
	if cint(dataent.db.get_single_value('System Settings', 'setup_complete')):
		for fn in dataent.get_hooks('get_user_progress_slides'):
			slides += dataent.get_attr(fn)()

	return slides

@dataent.whitelist()
def update_and_get_user_progress():
	'''
		Return setup progress action states (called via `update_and_get_user_progress` hook)
	'''
	states = {}
	for fn in dataent.get_hooks('update_and_get_user_progress'):
		states.update(dataent.get_attr(fn)())

	return states
