# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
import json,datetime
from six.moves.urllib.parse import parse_qs
from six import string_types, text_type
from dataent.utils import get_request_session
from dataent import _

def make_get_request(url, auth=None, headers=None, data=None):
	if not auth:
		auth = ''
	if not data:
		data = {}
	if not headers:
		headers = {}

	try:
		s = get_request_session()
		dataent.flags.integration_request = s.get(url, data={}, auth=auth, headers=headers)
		dataent.flags.integration_request.raise_for_status()
		return dataent.flags.integration_request.json()

	except Exception as exc:
		dataent.log_error(dataent.get_traceback())
		raise exc

def make_post_request(url, auth=None, headers=None, data=None):
	if not auth:
		auth = ''
	if not data:
		data = {}
	if not headers:
		headers = {}

	try:
		s = get_request_session()
		dataent.flags.integration_request = s.post(url, data=data, auth=auth, headers=headers)
		dataent.flags.integration_request.raise_for_status()

		if dataent.flags.integration_request.headers.get("content-type") == "text/plain; charset=utf-8":
			return parse_qs(dataent.flags.integration_request.text)

		return dataent.flags.integration_request.json()
	except Exception as exc:
		dataent.log_error()
		raise exc

def create_request_log(data, integration_type, service_name, name=None):
	if isinstance(data, string_types):
		data = json.loads(data)

	integration_request = dataent.get_doc({
		"doctype": "Integration Request",
		"integration_type": integration_type,
		"integration_request_service": service_name,
		"reference_doctype": data.get("reference_doctype"),
		"reference_docname": data.get("reference_docname"),
		"data": json.dumps(data, default=json_handler)
	})

	if name:
		integration_request.flags._name = name

	integration_request.insert(ignore_permissions=True)
	dataent.db.commit()

	return integration_request

def get_payment_gateway_controller(payment_gateway):
	'''Return payment gateway controller'''
	gateway = dataent.get_doc("Payment Gateway", payment_gateway)
	if gateway.gateway_controller is None:
		try:
			return dataent.get_doc("{0} Settings".format(payment_gateway))
		except Exception:
			dataent.throw(_("{0} Settings not found".format(payment_gateway)))
	else:
		try:
			return dataent.get_doc(gateway.gateway_settings, gateway.gateway_controller)
		except Exception:
			dataent.throw(_("{0} Settings not found".format(payment_gateway)))


@dataent.whitelist(allow_guest=True, xss_safe=True)
def get_checkout_url(**kwargs):
	try:
		if kwargs.get('payment_gateway'):
			doc = dataent.get_doc("{0} Settings".format(kwargs.get('payment_gateway')))
			return doc.get_payment_url(**kwargs)
		else:
			raise Exception
	except Exception:
		dataent.respond_as_web_page(_("Something went wrong"),
			_("Looks like something is wrong with this site's payment gateway configuration. No payment has been made."),
			indicator_color='red',
			http_status_code=dataent.ValidationError.http_status_code)

def create_payment_gateway(gateway, settings=None, controller=None):
	# NOTE: we don't translate Payment Gateway name because it is an internal doctype
	if not dataent.db.exists("Payment Gateway", gateway):
		payment_gateway = dataent.get_doc({
			"doctype": "Payment Gateway",
			"gateway": gateway,
			"gateway_settings": settings,
			"gateway_controller": controller
		})
		payment_gateway.insert(ignore_permissions=True)

def json_handler(obj):
	if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
		return text_type(obj)
