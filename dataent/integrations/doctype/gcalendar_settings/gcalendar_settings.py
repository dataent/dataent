# -*- coding: utf-8 -*-
# Copyright (c) 2018, DOKOS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent import _
from dataent.utils import get_request_site_address
import requests
import time
from dataent.utils.background_jobs import get_jobs

if dataent.conf.developer_mode:
	import os
	os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = 'https://www.googleapis.com/auth/calendar'
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"

class GCalendarSettings(Document):
	def sync(self):
		"""Create and execute Data Migration Run for GCalendar Sync plan"""
		dataent.has_permission('GCalendar Settings', throw=True)


		accounts = dataent.get_all("GCalendar Account", filters={'enabled': 1})

		queued_jobs = get_jobs(site=dataent.local.site, key='job_name')[dataent.local.site]
		for account in accounts:
			job_name = 'google_calendar_sync|{0}'.format(account.name)
			if job_name not in queued_jobs:
				dataent.enqueue('dataent.integrations.doctype.gcalendar_settings.gcalendar_settings.run_sync', queue='long', timeout=1500, job_name=job_name, account=account)
				time.sleep(5)

	def get_access_token(self):
		if not self.refresh_token:
			raise dataent.ValidationError(_("GCalendar is not configured."))
		data = {
			'client_id': self.client_id,
			'client_secret': self.get_password(fieldname='client_secret',raise_exception=False),
			'refresh_token': self.get_password(fieldname='refresh_token',raise_exception=False),
			'grant_type': "refresh_token",
			'scope': SCOPES
		}
		try:
			r = requests.post('https://www.googleapis.com/oauth2/v4/token', data=data).json()
		except requests.exceptions.HTTPError:
			dataent.throw(_("Something went wrong during the token generation. Please request again an authorization code."))
		return r.get('access_token')

@dataent.whitelist()
def sync():
	try:
		gcalendar_settings = dataent.get_doc('GCalendar Settings')
		if gcalendar_settings.enable == 1:
			gcalendar_settings.sync()
	except Exception:
		dataent.log_error(dataent.get_traceback())

def run_sync(account):
	exists = dataent.db.exists('Data Migration Run', dict(status=('in', ['Fail', 'Error'])))
	if exists:
		failed_run = dataent.get_doc("Data Migration Run", dict(status=('in', ['Fail', 'Error'])))
		failed_run.delete()

	started = dataent.db.exists('Data Migration Run', dict(status=('in', ['Started'])))
	if started:
		return

	try:
		doc = dataent.get_doc({
			'doctype': 'Data Migration Run',
			'data_migration_plan': 'GCalendar Sync',
			'data_migration_connector': 'Calendar Connector-' + account.name
		}).insert()
		try:
			doc.run()
		except Exception:
			dataent.log_error(dataent.get_traceback())
	except Exception:
		dataent.log_error(dataent.get_traceback())

@dataent.whitelist()
def google_callback(code=None, state=None, account=None):
	redirect_uri = get_request_site_address(True) + "?cmd=dataent.integrations.doctype.gcalendar_settings.gcalendar_settings.google_callback"
	if account is not None:
		dataent.cache().hset("gcalendar_account","GCalendar Account", account)
	doc = dataent.get_doc("GCalendar Settings")
	if code is None:
		return {
			'url': 'https://accounts.google.com/o/oauth2/v2/auth?access_type=offline&response_type=code&prompt=consent&client_id={}&include_granted_scopes=true&scope={}&redirect_uri={}'.format(doc.client_id, SCOPES, redirect_uri)
			}
	else:
		try:
			account = dataent.get_doc("GCalendar Account", dataent.cache().hget("gcalendar_account", "GCalendar Account"))
			data = {'code': code,
				'client_id': doc.client_id,
				'client_secret': doc.get_password(fieldname='client_secret',raise_exception=False),
				'redirect_uri': redirect_uri,
				'grant_type': 'authorization_code'}
			r = requests.post('https://www.googleapis.com/oauth2/v4/token', data=data).json()
			dataent.db.set_value("GCalendar Account", account.name, "authorization_code", code)
			if 'access_token' in r:
				dataent.db.set_value("GCalendar Account", account.name, "session_token", r['access_token'])
			if 'refresh_token' in r:
				dataent.db.set_value("GCalendar Account", account.name, "refresh_token", r['refresh_token'])
			dataent.db.commit()
			dataent.local.response["type"] = "redirect"
			dataent.local.response["location"] = "/integrations/gcalendar-success.html"
			return
		except Exception as e:
			dataent.throw(e.message)

@dataent.whitelist()
def refresh_token(token):
	if 'refresh_token' in token:
		dataent.db.set_value("GCalendar Settings", None, "refresh_token", token['refresh_token'])
	if 'access_token' in token:
		dataent.db.set_value("GCalendar Settings", None, "session_token", token['access_token'])
	dataent.db.commit()
