# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

"""
# Integrating RazorPay

### Validate Currency

Example:

	from dataent.integrations.utils import get_payment_gateway_controller

	controller = get_payment_gateway_controller("Razorpay")
	controller().validate_transaction_currency(currency)

### 2. Redirect for payment

Example:

	payment_details = {
		"amount": 600,
		"title": "Payment for bill : 111",
		"description": "payment via cart",
		"reference_doctype": "Payment Request",
		"reference_docname": "PR0001",
		"payer_email": "NuranVerkleij@example.com",
		"payer_name": "Nuran Verkleij",
		"order_id": "111",
		"currency": "INR",
		"payment_gateway": "Razorpay",
		"subscription_details": {
			"plan_id": "plan_12313", # if Required
			"start_date": "2018-08-30",
			"billing_period": "Month" #(Day, Week, Month, Year),
			"billing_frequency": 1,
			"customer_notify": 1,
			"upfront_amount": 1000
		}
	}

	# Redirect the user to this url
	url = controller().get_payment_url(**payment_details)


### 3. On Completion of Payment

Write a method for `on_payment_authorized` in the reference doctype

Example:

	def on_payment_authorized(payment_status):
		# this method will be called when payment is complete


##### Notes:

payment_status - payment gateway will put payment status on callback.
For razorpay payment status is Authorized

"""

from __future__ import unicode_literals
import dataent
from dataent import _
import json
from six.moves.urllib.parse import urlencode
from dataent.model.document import Document
from dataent.utils import get_url, call_hook_method, cint, get_timestamp
from dataent.integrations.utils import (make_get_request, make_post_request, create_request_log,
	create_payment_gateway)

class RazorpaySettings(Document):
	supported_currencies = ["INR"]

	def validate(self):
		create_payment_gateway('Razorpay')
		call_hook_method('payment_gateway_enabled', gateway='Razorpay')
		if not self.flags.ignore_mandatory:
			self.validate_razorpay_credentails()

	def validate_razorpay_credentails(self):
		if self.api_key and self.api_secret:
			try:
				make_get_request(url="https://api.razorpay.com/v1/payments",
					auth=(self.api_key, self.get_password(fieldname="api_secret", raise_exception=False)))
			except Exception:
				dataent.throw(_("Seems API Key or API Secret is wrong !!!"))

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			dataent.throw(_("Please select another payment method. Razorpay does not support transactions in currency '{0}'").format(currency))

	def setup_addon(self, settings, **kwargs):
		"""
			Addon template:
			{
				"item": {
					"name": row.upgrade_type,
					"amount": row.amount,
					"currency": currency,
					"description": "add-on description"
				},
				"quantity": 1 (The total amount is calculated as item.amount * quantity)
			}
		"""
		url = "https://api.razorpay.com/v1/subscriptions/{0}/addons".format(kwargs.get('subscription_id'))

		try:
			if not dataent.conf.converted_rupee_to_paisa:
				convert_rupee_to_paisa(**kwargs)

			for addon in kwargs.get("addons"):
				resp = make_post_request(
					url,
					auth=(settings.api_key, settings.api_secret),
					data=json.dumps(addon),
					headers={
						"content-type": "application/json"
					}
				)
				if not resp.get('id'):
					dataent.log_error(str(resp), 'Razorpay Failed while creating subscription')
		except:
			dataent.log_error(dataent.get_traceback())
			# failed
			pass

	def setup_subscription(self, settings, **kwargs):
		start_date = get_timestamp(kwargs.get('subscription_details').get("start_date")) \
			if kwargs.get('subscription_details').get("start_date") else None

		subscription_details = {
			"plan_id": kwargs.get('subscription_details').get("plan_id"),
			"start_at": cint(start_date),
			"total_count": kwargs.get('subscription_details').get("billing_frequency"),
			"customer_notify": kwargs.get('subscription_details').get("customer_notify")
		}

		if kwargs.get('addons'):
			convert_rupee_to_paisa(**kwargs)
			subscription_details.update({
				"addons": kwargs.get('addons')
			})

		try:
			resp = make_post_request(
				"https://api.razorpay.com/v1/subscriptions",
				auth=(settings.api_key, settings.api_secret),
				data=json.dumps(subscription_details),
				headers={
					"content-type": "application/json"
				}
			)

			if resp.get('status') == 'created':
				kwargs['subscription_id'] = resp.get('id')
				dataent.flags.status = 'created'
				return kwargs
			else:
				dataent.log_error(str(resp), 'Razorpay Failed while creating subscription')

		except:
			dataent.log_error(dataent.get_traceback())
			# failed
			pass

	def prepare_subscription_details(self, settings, **kwargs):
		if not kwargs.get("subscription_id"):
			kwargs = self.setup_subscription(settings, **kwargs)

		if dataent.flags.status !='created':
			kwargs['subscription_id'] = None

		return kwargs

	def get_payment_url(self, **kwargs):
		integration_request = create_request_log(kwargs, "Host", "Razorpay")
		return get_url("./integrations/razorpay_checkout?token={0}".format(integration_request.name))

	def create_request(self, data):
		self.data = dataent._dict(data)

		try:
			self.integration_request = dataent.get_doc("Integration Request", self.data.token)
			self.integration_request.update_status(self.data, 'Queued')
			return self.authorize_payment()

		except Exception:
			dataent.log_error(dataent.get_traceback())
			return{
				"redirect_to": dataent.redirect_to_message(_('Server Error'), _("Seems issue with server's razorpay config. Don't worry, in case of failure amount will get refunded to your account.")),
				"status": 401
			}

	def authorize_payment(self):
		"""
		An authorization is performed when user’s payment details are successfully authenticated by the bank.
		The money is deducted from the customer’s account, but will not be transferred to the merchant’s account
		until it is explicitly captured by merchant.
		"""
		data = json.loads(self.integration_request.data)
		settings = self.get_settings(data)

		try:
			resp = make_get_request("https://api.razorpay.com/v1/payments/{0}"
				.format(self.data.razorpay_payment_id), auth=(settings.api_key,
					settings.api_secret))

			if resp.get("status") == "authorized":
				self.integration_request.update_status(data, 'Authorized')
				self.flags.status_changed_to = "Authorized"

			elif data.get('subscription_id'):
				if resp.get("status") == "refunded":
					# if subscription start date is in future then
					# razorpay refunds the amount after authorizing the card details
					# thus changing status to Verified

					self.integration_request.update_status(data, 'Completed')
					self.flags.status_changed_to = "Verified"

				if resp.get("status") == "captured":
					# if subscription starts immediately then
					# razorpay charge the actual amount
					# thus changing status to Completed

					self.integration_request.update_status(data, 'Completed')
					self.flags.status_changed_to = "Completed"

			else:
				dataent.log_error(str(resp), 'Razorpay Payment not authorized')

		except:
			dataent.log_error(dataent.get_traceback())
			# failed
			pass

		status = dataent.flags.integration_request.status_code

		redirect_to = data.get('notes', {}).get('redirect_to') or None
		redirect_message = data.get('notes', {}).get('redirect_message') or None

		if self.flags.status_changed_to in ("Authorized", "Verified", "Completed"):
			if self.data.reference_doctype and self.data.reference_docname:
				custom_redirect_to = None
				try:
					dataent.flags.data = data
					custom_redirect_to = dataent.get_doc(self.data.reference_doctype,
						self.data.reference_docname).run_method("on_payment_authorized", self.flags.status_changed_to)

				except Exception:
					dataent.log_error(dataent.get_traceback())

				if custom_redirect_to:
					redirect_to = custom_redirect_to

			redirect_url = 'payment-success?doctype={0}&docname={1}'.format(self.data.reference_doctype, self.data.reference_docname)
		else:
			redirect_url = 'payment-failed'

		if redirect_to:
			redirect_url += '&' + urlencode({'redirect_to': redirect_to})
		if redirect_message:
			redirect_url += '&' + urlencode({'redirect_message': redirect_message})

		return {
			"redirect_to": redirect_url,
			"status": status
		}

	def get_settings(self, data):
		settings = dataent._dict({
			"api_key": self.api_key,
			"api_secret": self.get_password(fieldname="api_secret", raise_exception=False)
		})

		if cint(data.get('notes', {}).get('use_sandbox')) or data.get("use_sandbox"):
			settings.update({
				"api_key": dataent.conf.sandbox_api_key,
				"api_secret": dataent.conf.sandbox_api_secret,
			})

		return settings

	def cancel_subscription(self, subscription_id):
		settings = self.get_settings({})

		try:
			resp = make_post_request("https://api.razorpay.com/v1/subscriptions/{0}/cancel"
				.format(subscription_id), auth=(settings.api_key,
					settings.api_secret))
		except Exception:
			dataent.log_error(dataent.get_traceback())

def capture_payment(is_sandbox=False, sanbox_response=None):
	"""
		Verifies the purchase as complete by the merchant.
		After capture, the amount is transferred to the merchant within T+3 days
		where T is the day on which payment is captured.

		Note: Attempting to capture a payment whose status is not authorized will produce an error.
	"""
	controller = dataent.get_doc("Razorpay Settings")

	for doc in dataent.get_all("Integration Request", filters={"status": "Authorized",
		"integration_request_service": "Razorpay"}, fields=["name", "data"]):
		try:
			if is_sandbox:
				resp = sanbox_response
			else:
				data = json.loads(doc.data)
				settings = controller.get_settings(data)

				resp = make_get_request("https://api.razorpay.com/v1/payments/{0}".format(data.get("razorpay_payment_id")),
					auth=(settings.api_key, settings.api_secret), data={"amount": data.get("amount")})

				if resp.get('status') == "authorized":
					resp = make_post_request("https://api.razorpay.com/v1/payments/{0}/capture".format(data.get("razorpay_payment_id")),
						auth=(settings.api_key, settings.api_secret), data={"amount": data.get("amount")})

			if resp.get("status") == "captured":
				dataent.db.set_value("Integration Request", doc.name, "status", "Completed")

		except Exception:
			doc = dataent.get_doc("Integration Request", doc.name)
			doc.status = "Failed"
			doc.error = dataent.get_traceback()
			dataent.log_error(doc.error, '{0} Failed'.format(doc.name))

def convert_rupee_to_paisa(**kwargs):
	for addon in kwargs.get('addons'):
		addon['item']['amount'] *= 100

	dataent.conf.converted_rupee_to_paisa = True

@dataent.whitelist(allow_guest=True)
def razorpay_subscription_callback():
	try:
		data = dataent.local.form_dict

		validate_payment_callback(data)

		data.update({
			"payment_gateway": "Razorpay"
		})

		doc = dataent.get_doc({
			"data": json.dumps(dataent.local.form_dict),
			"doctype": "Integration Request",
			"integration_type": "Subscription Notification",
			"status": "Queued"
		}).insert(ignore_permissions=True)
		dataent.db.commit()

		dataent.enqueue(method='dataent.integrations.doctype.razorpay_settings.razorpay_settings.handle_subscription_notification',
			queue='long', timeout=600, is_async=True, **{"doctype": "Integration Request", "docname":  doc.name})

	except dataent.InvalidStatusError:
		pass
	except Exception as e:
		dataent.log(dataent.log_error(title=e))

def validate_payment_callback(data):
	def _throw():
		dataent.throw(_("Invalid Subscription"), exc=dataent.InvalidStatusError)

	subscription_id = data.get('payload').get("subscription").get("entity").get("id")

	if not(subscription_id):
		_throw()

	controller = dataent.get_doc("Razorpay Settings")

	settings = controller.get_settings(data)

	resp = make_get_request("https://api.razorpay.com/v1/subscriptions/{0}".format(subscription_id),
		auth=(settings.api_key, settings.api_secret))

	if resp.get("status") != "active":
		_throw()

def handle_subscription_notification(doctype, docname):
	call_hook_method("handle_subscription_notification", doctype=doctype, docname=docname)