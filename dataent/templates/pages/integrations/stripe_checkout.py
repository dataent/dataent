# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.utils import cint, fmt_money
import json
from dataent.integrations.doctype.stripe_settings.stripe_settings import get_gateway_controller

no_cache = 1
no_sitemap = 1

expected_keys = ('amount', 'title', 'description', 'reference_doctype', 'reference_docname',
	'payer_name', 'payer_email', 'order_id', 'currency')

def get_context(context):
	context.no_cache = 1

	# all these keys exist in form_dict
	if not (set(expected_keys) - set(list(dataent.form_dict))):
		for key in expected_keys:
			context[key] = dataent.form_dict[key]

		gateway_controller = get_gateway_controller(context.reference_doctype, context.reference_docname)
		context.publishable_key = get_api_key(context.reference_docname, gateway_controller)
		context.image = get_header_image(context.reference_docname, gateway_controller)

		context['amount'] = fmt_money(amount=context['amount'], currency=context['currency'])

		if dataent.db.get_value(context.reference_doctype, context.reference_docname, "is_a_subscription"):
			payment_plan = dataent.db.get_value(context.reference_doctype, context.reference_docname, "payment_plan")
			recurrence = dataent.db.get_value("Payment Plan", payment_plan, "recurrence")

			context['amount'] = context['amount'] + " " + _(recurrence)

	else:
		dataent.redirect_to_message(_('Some information is missing'),
			_('Looks like someone sent you to an incomplete URL. Please ask them to look into it.'))
		dataent.local.flags.redirect_location = dataent.local.response.location
		raise dataent.Redirect

def get_api_key(doc, gateway_controller):
	publishable_key = dataent.db.get_value("Stripe Settings", gateway_controller, "publishable_key")
	if cint(dataent.form_dict.get("use_sandbox")):
		publishable_key = dataent.conf.sandbox_publishable_key

	return publishable_key

def get_header_image(doc, gateway_controller):
	header_image = dataent.db.get_value("Stripe Settings", gateway_controller, "header_img")

	return header_image

@dataent.whitelist(allow_guest=True)
def make_payment(stripe_token_id, data, reference_doctype=None, reference_docname=None):
	data = json.loads(data)

	data.update({
		"stripe_token_id": stripe_token_id
	})

	gateway_controller = get_gateway_controller(reference_doctype,reference_docname)

	if dataent.db.get_value(reference_doctype, reference_docname, 'is_a_subscription'):
		reference = dataent.get_doc(reference_doctype, reference_docname)
		data =  reference.create_subscription("stripe", gateway_controller, data)
	else:
		data =  dataent.get_doc("Stripe Settings", gateway_controller).create_request(data)

	dataent.db.commit()
	return data
