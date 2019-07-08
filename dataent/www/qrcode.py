# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import dataent
from dataent import _
from six.moves.urllib.parse import parse_qs
from dataent.twofactor import get_qr_svg_code

def get_context(context):
	context.no_cache = 1
	context.qr_code_user,context.qrcode_svg = get_user_svg_from_cache()

def get_query_key():
	'''Return query string arg.'''
	query_string = dataent.local.request.query_string
	query = parse_qs(query_string)
	if not 'k' in list(query):
		dataent.throw(_('Not Permitted'),dataent.PermissionError)
	query = (query['k'][0]).strip()
	if False in [i.isalpha() or i.isdigit() for i in query]:
		dataent.throw(_('Not Permitted'),dataent.PermissionError)
	return query

def get_user_svg_from_cache():
	'''Get User and SVG code from cache.'''
	key = get_query_key()
	totp_uri = dataent.cache().get_value("{}_uri".format(key))
	user = dataent.cache().get_value("{}_user".format(key))
	if not totp_uri or not user:
		dataent.throw(_('Page has expired!'),dataent.PermissionError)
	if not dataent.db.exists('User',user):
		dataent.throw(_('Not Permitted'), dataent.PermissionError)
	user = dataent.get_doc('User',user)
	svg = get_qr_svg_code(totp_uri)
	return (user,svg)
