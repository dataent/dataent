# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
import dataent.utils
from dataent.utils.oauth import login_via_oauth2, login_via_oauth2_id_token
import json

@dataent.whitelist(allow_guest=True)
def login_via_google(code, state):
	login_via_oauth2("google", code, state, decoder=json.loads)

@dataent.whitelist(allow_guest=True)
def login_via_github(code, state):
	login_via_oauth2("github", code, state)

@dataent.whitelist(allow_guest=True)
def login_via_facebook(code, state):
	login_via_oauth2("facebook", code, state, decoder=json.loads)

@dataent.whitelist(allow_guest=True)
def login_via_dataent(code, state):
	login_via_oauth2("dataent", code, state, decoder=json.loads)

@dataent.whitelist(allow_guest=True)
def login_via_office365(code, state):
	login_via_oauth2_id_token("office_365", code, state, decoder=json.loads)

@dataent.whitelist(allow_guest=True)
def login_via_salesforce(code, state):
	login_via_oauth2("salesforce", code, state, decoder=json.loads)

@dataent.whitelist(allow_guest=True)
def custom(code, state):
	"""
	Callback for processing code and state for user added providers

	process social login from /api/method/dataent.integrations.custom/<provider>
	"""
	path = dataent.request.path[1:].split("/")
	if len(path) == 4 and path[3]:
		provider = path[3]
		# Validates if provider doctype exists
		if dataent.db.exists("Social Login Key", provider):
			login_via_oauth2(provider, code, state, decoder=json.loads)
