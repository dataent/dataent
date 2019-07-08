from __future__ import unicode_literals
import dataent, json
from dataent.oauth import OAuthWebRequestValidator, WebApplicationServer
from oauthlib.oauth2 import FatalClientError, OAuth2Error
from werkzeug import url_fix
from six.moves.urllib.parse import quote, urlencode, urlparse
from dataent.integrations.doctype.oauth_provider_settings.oauth_provider_settings import get_oauth_settings
from dataent import _

def get_oauth_server():
	if not getattr(dataent.local, 'oauth_server', None):
		oauth_validator = OAuthWebRequestValidator()
		dataent.local.oauth_server  = WebApplicationServer(oauth_validator)

	return dataent.local.oauth_server

def get_urlparams_from_kwargs(param_kwargs):
	arguments = param_kwargs
	if arguments.get("data"):
		arguments.pop("data")
	if arguments.get("cmd"):
		arguments.pop("cmd")

	return urlencode(arguments)

@dataent.whitelist()
def approve(*args, **kwargs):
	r = dataent.request
	uri = url_fix(r.url.replace("+"," "))
	http_method = r.method
	body = r.get_data()
	headers = r.headers

	try:
		scopes, dataent.flags.oauth_credentials = get_oauth_server().validate_authorization_request(uri, http_method, body, headers)

		headers, body, status = get_oauth_server().create_authorization_response(uri=dataent.flags.oauth_credentials['redirect_uri'], \
				body=body, headers=headers, scopes=scopes, credentials=dataent.flags.oauth_credentials)
		uri = headers.get('Location', None)

		dataent.local.response["type"] = "redirect"
		dataent.local.response["location"] = uri

	except FatalClientError as e:
		return e
	except OAuth2Error as e:
		return e

@dataent.whitelist(allow_guest=True)
def authorize(*args, **kwargs):
	#Fetch provider URL from settings
	oauth_settings = get_oauth_settings()
	params = get_urlparams_from_kwargs(kwargs)
	request_url = urlparse(dataent.request.url)
	success_url = request_url.scheme + "://" + request_url.netloc + "/api/method/dataent.integrations.oauth2.approve?" + params
	failure_url = dataent.form_dict["redirect_uri"] + "?error=access_denied"

	if dataent.session['user']=='Guest':
		#Force login, redirect to preauth again.
		dataent.local.response["type"] = "redirect"
		dataent.local.response["location"] = "/login?redirect-to=/api/method/dataent.integrations.oauth2.authorize?" + quote(params.replace("+"," "))

	elif dataent.session['user']!='Guest':
		try:
			r = dataent.request
			uri = url_fix(r.url)
			http_method = r.method
			body = r.get_data()
			headers = r.headers

			scopes, dataent.flags.oauth_credentials = get_oauth_server().validate_authorization_request(uri, http_method, body, headers)

			skip_auth = dataent.db.get_value("OAuth Client", dataent.flags.oauth_credentials['client_id'], "skip_authorization")
			unrevoked_tokens = dataent.get_all("OAuth Bearer Token", filters={"status":"Active"})

			if skip_auth or (oauth_settings["skip_authorization"] == "Auto" and len(unrevoked_tokens)):

				dataent.local.response["type"] = "redirect"
				dataent.local.response["location"] = success_url
			else:
				#Show Allow/Deny screen.
				response_html_params = dataent._dict({
					"client_id": dataent.db.get_value("OAuth Client", kwargs['client_id'], "app_name"),
					"success_url": success_url,
					"failure_url": failure_url,
					"details": scopes
				})
				resp_html = dataent.render_template("templates/includes/oauth_confirmation.html", response_html_params)
				dataent.respond_as_web_page("Confirm Access", resp_html)

		except FatalClientError as e:
			return e
		except OAuth2Error as e:
			return e

@dataent.whitelist(allow_guest=True)
def get_token(*args, **kwargs):
	r = dataent.request

	uri = url_fix(r.url)
	http_method = r.method
	body = r.form
	headers = r.headers
	
	#Check whether dataent server URL is set
	dataent_server_url = dataent.db.get_value("Social Login Key", "dataent", "base_url") or None
	if not dataent_server_url:
		dataent.throw(_("Please set Base URL in Social Login Key for Dataent"))

	try:
		headers, body, status = get_oauth_server().create_token_response(uri, http_method, body, headers, dataent.flags.oauth_credentials)
		out = dataent._dict(json.loads(body))
		if not out.error and "openid" in out.scope:
			token_user = dataent.db.get_value("OAuth Bearer Token", out.access_token, "user")
			token_client = dataent.db.get_value("OAuth Bearer Token", out.access_token, "client")
			client_secret = dataent.db.get_value("OAuth Client", token_client, "client_secret")
			if token_user in ["Guest", "Administrator"]:
				dataent.throw(_("Logged in as Guest or Administrator"))
			import hashlib
			id_token_header = {
				"typ":"jwt",
				"alg":"HS256"
			}
			id_token = {
				"aud": token_client,
				"exp": int((dataent.db.get_value("OAuth Bearer Token", out.access_token, "expiration_time") - dataent.utils.datetime.datetime(1970, 1, 1)).total_seconds()),
				"sub": dataent.db.get_value("User Social Login", {"parent":token_user, "provider": "dataent"}, "userid"),
				"iss": dataent_server_url,
				"at_hash": dataent.oauth.calculate_at_hash(out.access_token, hashlib.sha256)
			}
			import jwt
			id_token_encoded = jwt.encode(id_token, client_secret, algorithm='HS256', headers=id_token_header)
			out.update({"id_token":str(id_token_encoded)})
		dataent.local.response = out

	except FatalClientError as e:
		return e


@dataent.whitelist(allow_guest=True)
def revoke_token(*args, **kwargs):
	r = dataent.request
	uri = url_fix(r.url)
	http_method = r.method
	body = r.form
	headers = r.headers

	headers, body, status = get_oauth_server().create_revocation_response(uri, headers=headers, body=body, http_method=http_method)

	dataent.local.response['http_status_code'] = status
	if status == 200:
		return "success"
	else:
		return "bad request"

@dataent.whitelist()
def openid_profile(*args, **kwargs):
	picture = None
	first_name, last_name, avatar, name = dataent.db.get_value("User", dataent.session.user, ["first_name", "last_name", "user_image", "name"])
	dataent_userid = dataent.db.get_value("User Social Login", {"parent":dataent.session.user, "provider": "dataent"}, "userid")
	request_url = urlparse(dataent.request.url)

	if avatar:
		if validate_url(avatar):
			picture = avatar
		else:
			picture = request_url.scheme + "://" + request_url.netloc + avatar

	user_profile = dataent._dict({
			"sub": dataent_userid,
			"name": " ".join(filter(None, [first_name, last_name])),
			"given_name": first_name,
			"family_name": last_name,
			"email": name,
			"picture": picture
		})
	
	dataent.local.response = user_profile

def validate_url(url_string):
	try:
		result = urlparse(url_string)
		if result.scheme and result.scheme in ["http", "https", "ftp", "ftps"]:
			return True
		else:
			return False
	except:
		return False