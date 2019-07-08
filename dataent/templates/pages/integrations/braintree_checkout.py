# Copyright (c) 2018, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.utils import flt
import json
from dataent.integrations.doctype.braintree_settings.braintree_settings import get_client_token, get_gateway_controller

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

		context.client_token = get_client_token(context.reference_docname)

		context['amount'] = flt(context['amount'])

		gateway_controller = get_gateway_controller(context.reference_docname)
		context['header_img'] = dataent.db.get_value("Braintree Settings", gateway_controller, "header_img")

	else:
		dataent.redirect_to_message(_('Some information is missing'),
			_('Looks like someone sent you to an incomplete URL. Please ask them to look into it.'))
		dataent.local.flags.redirect_location = dataent.local.response.location
		raise dataent.Redirect

@dataent.whitelist(allow_guest=True)
def make_payment(payload_nonce, data, reference_doctype, reference_docname):
	data = json.loads(data)

	data.update({
		"payload_nonce": payload_nonce
	})

	gateway_controller = get_gateway_controller(reference_docname)
	data =  dataent.get_doc("Braintree Settings", gateway_controller).create_payment_request(data)
	dataent.db.commit()
	return data
