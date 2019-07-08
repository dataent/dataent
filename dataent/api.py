# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import json
import dataent
import dataent.handler
import dataent.client
from dataent.utils.response import build_response
from dataent import _
from six.moves.urllib.parse import urlparse, urlencode
import base64


def handle():
	"""
	Handler for `/api` methods

	### Examples:

	`/api/method/{methodname}` will call a whitelisted method

	`/api/resource/{doctype}` will query a table
		examples:
		- `?fields=["name", "owner"]`
		- `?filters=[["Task", "name", "like", "%005"]]`
		- `?limit_start=0`
		- `?limit_page_length=20`

	`/api/resource/{doctype}/{name}` will point to a resource
		`GET` will return doclist
		`POST` will insert
		`PUT` will update
		`DELETE` will delete

	`/api/resource/{doctype}/{name}?run_method={method}` will run a whitelisted controller method
	"""

	validate_oauth()
	validate_auth_via_api_keys()

	parts = dataent.request.path[1:].split("/",3)
	call = doctype = name = None

	if len(parts) > 1:
		call = parts[1]

	if len(parts) > 2:
		doctype = parts[2]

	if len(parts) > 3:
		name = parts[3]

	if call=="method":
		dataent.local.form_dict.cmd = doctype
		return dataent.handler.handle()

	elif call=="resource":
		if "run_method" in dataent.local.form_dict:
			method = dataent.local.form_dict.pop("run_method")
			doc = dataent.get_doc(doctype, name)
			doc.is_whitelisted(method)

			if dataent.local.request.method=="GET":
				if not doc.has_permission("read"):
					dataent.throw(_("Not permitted"), dataent.PermissionError)
				dataent.local.response.update({"data": doc.run_method(method, **dataent.local.form_dict)})

			if dataent.local.request.method=="POST":
				if not doc.has_permission("write"):
					dataent.throw(_("Not permitted"), dataent.PermissionError)

				dataent.local.response.update({"data": doc.run_method(method, **dataent.local.form_dict)})
				dataent.db.commit()

		else:
			if name:
				if dataent.local.request.method=="GET":
					doc = dataent.get_doc(doctype, name)
					if not doc.has_permission("read"):
						raise dataent.PermissionError
					dataent.local.response.update({"data": doc})

				if dataent.local.request.method=="PUT":
					data = json.loads(dataent.local.form_dict.data)
					doc = dataent.get_doc(doctype, name)

					if "flags" in data:
						del data["flags"]

					# Not checking permissions here because it's checked in doc.save
					doc.update(data)

					dataent.local.response.update({
						"data": doc.save().as_dict()
					})
					dataent.db.commit()

				if dataent.local.request.method=="DELETE":
					# Not checking permissions here because it's checked in delete_doc
					dataent.delete_doc(doctype, name, ignore_missing=False)
					dataent.local.response.http_status_code = 202
					dataent.local.response.message = "ok"
					dataent.db.commit()


			elif doctype:
				if dataent.local.request.method=="GET":
					if dataent.local.form_dict.get('fields'):
						dataent.local.form_dict['fields'] = json.loads(dataent.local.form_dict['fields'])
					dataent.local.form_dict.setdefault('limit_page_length', 20)
					dataent.local.response.update({
						"data":  dataent.call(dataent.client.get_list,
							doctype, **dataent.local.form_dict)})

				if dataent.local.request.method=="POST":
					data = json.loads(dataent.local.form_dict.data)
					data.update({
						"doctype": doctype
					})
					dataent.local.response.update({
						"data": dataent.get_doc(data).insert().as_dict()
					})
					dataent.db.commit()
			else:
				raise dataent.DoesNotExistError

	else:
		raise dataent.DoesNotExistError

	return build_response("json")

def validate_oauth():
	from dataent.oauth import get_url_delimiter
	form_dict = dataent.local.form_dict
	authorization_header = dataent.get_request_header("Authorization").split(" ") if dataent.get_request_header("Authorization") else None
	if authorization_header and authorization_header[0].lower() == "bearer":
		from dataent.integrations.oauth2 import get_oauth_server
		token = authorization_header[1]
		r = dataent.request
		parsed_url = urlparse(r.url)
		access_token = { "access_token": token}
		uri = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
		http_method = r.method
		body = r.get_data()
		headers = r.headers

		required_scopes = dataent.db.get_value("OAuth Bearer Token", token, "scopes").split(get_url_delimiter())

		valid, oauthlib_request = get_oauth_server().verify_request(uri, http_method, body, headers, required_scopes)

		if valid:
			dataent.set_user(dataent.db.get_value("OAuth Bearer Token", token, "user"))
			dataent.local.form_dict = form_dict


def validate_auth_via_api_keys():
	"""
	authentication using api key and api secret

	set user
	"""
	try:
		authorization_header = dataent.get_request_header("Authorization", None).split(" ") if dataent.get_request_header("Authorization") else None
		if authorization_header and authorization_header[0] == 'Basic':
			token = dataent.safe_decode(base64.b64decode(authorization_header[1])).split(":")
			validate_api_key_secret(token[0], token[1])
		elif authorization_header and authorization_header[0] == 'token':
			token = authorization_header[1].split(":")
			validate_api_key_secret(token[0], token[1])
	except Exception as e:
		raise e

def validate_api_key_secret(api_key, api_secret):
	user = dataent.db.get_value(
		doctype="User",
		filters={"api_key": api_key},
		fieldname=['name']
	)
	form_dict = dataent.local.form_dict
	user_secret = dataent.utils.password.get_decrypted_password ("User", user, fieldname='api_secret')
	if api_secret == user_secret:
		dataent.set_user(user)
		dataent.local.form_dict = form_dict