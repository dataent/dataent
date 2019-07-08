# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function
import dataent
from dataent.model.document import Document
from dataent.utils import cint, has_gravatar, format_datetime, now_datetime, get_formatted_email
from dataent import throw, msgprint, _
from dataent.utils.password import update_password as _update_password
from dataent.desk.notifications import clear_notifications
from dataent.utils.user import get_system_managers
import dataent.permissions
import dataent.share
import re
from dataent.limits import get_limits
from dataent.website.utils import is_signup_enabled
from dataent.utils.background_jobs import enqueue

STANDARD_USERS = ("Guest", "Administrator")

class MaxUsersReachedError(dataent.ValidationError): pass

class User(Document):
	__new_password = None

	def __setup__(self):
		# because it is handled separately
		self.flags.ignore_save_passwords = ['new_password']

	def autoname(self):
		"""set name as Email Address"""
		if self.get("is_admin") or self.get("is_guest"):
			self.name = self.first_name
		else:
			self.email = self.email.strip()
			self.name = self.email

	def onload(self):
		self.set_onload('all_modules',
			[m.module_name for m in dataent.db.get_all('Desktop Icon',
				fields=['module_name'], filters={'standard': 1}, order_by="module_name")])

	def before_insert(self):
		self.flags.in_insert = True
		throttle_user_creation()

	def validate(self):
		self.check_demo()

		# clear new password
		self.__new_password = self.new_password
		self.new_password = ""

		if not dataent.flags.in_test:
			self.password_strength_test()

		if self.name not in STANDARD_USERS:
			self.validate_email_type(self.email)
			self.validate_email_type(self.name)
		self.add_system_manager_role()
		self.set_system_user()
		self.set_full_name()
		self.check_enable_disable()
		self.ensure_unique_roles()
		self.remove_all_roles_for_guest()
		self.validate_username()
		self.remove_disabled_roles()
		self.validate_user_email_inbox()
		ask_pass_update()
		self.validate_roles()
		self.validate_user_image()

		if self.language == "Loading...":
			self.language = None

		if (self.name not in ["Administrator", "Guest"]) and (not self.get_social_login_userid("dataent")):
			self.set_social_login_userid("dataent", dataent.generate_hash(length=39))

	def validate_roles(self):
		if self.role_profile_name:
				role_profile = dataent.get_doc('Role Profile', self.role_profile_name)
				self.set('roles', [])
				self.append_roles(*[role.role for role in role_profile.roles])

	def validate_user_image(self):
		if self.user_image and len(self.user_image) > 2000:
			dataent.throw(_("Not a valid User Image."))

	def on_update(self):
		# clear new password
		self.validate_user_limit()
		self.share_with_self()
		clear_notifications(user=self.name)
		dataent.clear_cache(user=self.name)
		self.send_password_notification(self.__new_password)
		create_contact(self, ignore_mandatory=True)
		if self.name not in ('Administrator', 'Guest') and not self.user_image:
			dataent.enqueue('dataent.core.doctype.user.user.update_gravatar', name=self.name)

	def has_website_permission(self, ptype, user, verbose=False):
		"""Returns true if current user is the session user"""
		return self.name == dataent.session.user

	def check_demo(self):
		if dataent.session.user == 'demo@epaas.xyz':
			dataent.throw(_('Cannot change user details in demo. Please signup for a new account at https://epaas.xyz'), title=_('Not Allowed'))

	def set_full_name(self):
		self.full_name = " ".join(filter(None, [self.first_name, self.last_name]))

	def check_enable_disable(self):
		# do not allow disabling administrator/guest
		if not cint(self.enabled) and self.name in STANDARD_USERS:
			dataent.throw(_("User {0} cannot be disabled").format(self.name))

		if not cint(self.enabled):
			self.a_system_manager_should_exist()

		# clear sessions if disabled
		if not cint(self.enabled) and getattr(dataent.local, "login_manager", None):
			dataent.local.login_manager.logout(user=self.name)

	def add_system_manager_role(self):
		# if adding system manager, do nothing
		if not cint(self.enabled) or ("System Manager" in [user_role.role for user_role in
				self.get("roles")]):
			return

		if (self.name not in STANDARD_USERS and self.user_type == "System User" and not self.get_other_system_managers()
			and cint(dataent.db.get_single_value('System Settings', 'setup_complete'))):

			msgprint(_("Adding System Manager to this User as there must be atleast one System Manager"))
			self.append("roles", {
				"doctype": "Has Role",
				"role": "System Manager"
			})

		if self.name == 'Administrator':
			# Administrator should always have System Manager Role
			self.extend("roles", [
				{
					"doctype": "Has Role",
					"role": "System Manager"
				},
				{
					"doctype": "Has Role",
					"role": "Administrator"
				}
			])

	def email_new_password(self, new_password=None):
		if new_password and not self.flags.in_insert:
			_update_password(user=self.name, pwd=new_password, logout_all_sessions=self.logout_all_sessions)

			if self.send_password_update_notification and self.enabled:
				self.password_update_mail(new_password)
				dataent.msgprint(_("New password emailed"))

	def set_system_user(self):
		'''Set as System User if any of the given roles has desk_access'''
		if self.has_desk_access() or self.name == 'Administrator':
			self.user_type = 'System User'
		else:
			self.user_type = 'Website User'

	def has_desk_access(self):
		'''Return true if any of the set roles has desk access'''
		if not self.roles:
			return False

		return len(dataent.db.sql("""select name
			from `tabRole` where desk_access=1
				and name in ({0}) limit 1""".format(', '.join(['%s'] * len(self.roles))),
				[d.role for d in self.roles]))


	def share_with_self(self):
		if self.user_type=="System User":
			dataent.share.add(self.doctype, self.name, self.name, write=1, share=1,
				flags={"ignore_share_permission": True})
		else:
			dataent.share.remove(self.doctype, self.name, self.name,
				flags={"ignore_share_permission": True, "ignore_permissions": True})

	def validate_share(self, docshare):
		if docshare.user == self.name:
			if self.user_type=="System User":
				if docshare.share != 1:
					dataent.throw(_("Sorry! User should have complete access to their own record."))
			else:
				dataent.throw(_("Sorry! Sharing with Website User is prohibited."))

	def send_password_notification(self, new_password):
		try:
			if self.flags.in_insert:
				if self.name not in STANDARD_USERS:
					if new_password:
						# new password given, no email required
						_update_password(user=self.name, pwd=new_password,
							logout_all_sessions=self.logout_all_sessions)

					if not self.flags.no_welcome_mail and self.send_welcome_email:
						self.send_welcome_mail_to_user()
						self.flags.email_sent = 1
						if dataent.session.user != 'Guest':
							msgprint(_("Welcome email sent"))
						return
			else:
				self.email_new_password(new_password)

		except dataent.OutgoingEmailError:
			print(dataent.get_traceback())
			pass # email server not set, don't send email

	@Document.hook
	def validate_reset_password(self):
		pass

	def reset_password(self, send_email=False):
		from dataent.utils import random_string, get_url

		key = random_string(32)
		self.db_set("reset_password_key", key)
		link = get_url("/update-password?key=" + key)

		if send_email:
			self.password_reset_mail(link)

		return link

	def get_other_system_managers(self):
		return dataent.db.sql("""select distinct user.name from `tabHas Role` user_role, tabUser user
			where user_role.role='System Manager'
				and user.docstatus<2
				and user.enabled=1
				and user_role.parent = user.name
			and user_role.parent not in ('Administrator', %s) limit 1""", (self.name,))

	def get_fullname(self):
		"""get first_name space last_name"""
		return (self.first_name or '') + \
			(self.first_name and " " or '') + (self.last_name or '')

	def password_reset_mail(self, link):
		self.send_login_mail(_("Password Reset"),
			"password_reset", {"link": link}, now=True)

	def password_update_mail(self, password):
		self.send_login_mail(_("Password Update"),
			"password_update", {"new_password": password}, now=True)

	def send_welcome_mail_to_user(self):
		from dataent.utils import get_url
		link = self.reset_password()
		subject = None
		method = dataent.get_hooks("welcome_email")
		if method:
			subject = dataent.get_attr(method[-1])()
		if not subject:
			site_name = dataent.db.get_default('site_name') or dataent.get_conf().get("site_name")
			if site_name:
				subject = _("Welcome to {0}".format(site_name))
			else:
				subject = _("Complete Registration")

		self.send_login_mail(subject, "new_user",
				dict(
					link=link,
					site_url=get_url(),
				))

	def send_login_mail(self, subject, template, add_args, now=None):
		"""send mail with login details"""
		from dataent.utils.user import get_user_fullname
		from dataent.utils import get_url

		full_name = get_user_fullname(dataent.session['user'])
		if full_name == "Guest":
			full_name = "Administrator"

		args = {
			'first_name': self.first_name or self.last_name or "user",
			'user': self.name,
			'title': subject,
			'login_url': get_url(),
			'user_fullname': full_name
		}

		args.update(add_args)

		sender = dataent.session.user not in STANDARD_USERS and get_formatted_email(dataent.session.user) or None

		dataent.sendmail(recipients=self.email, sender=sender, subject=subject,
			template=template, args=args, header=[subject, "green"],
			delayed=(not now) if now!=None else self.flags.delay_emails, retry=3)

	def a_system_manager_should_exist(self):
		if not self.get_other_system_managers():
			throw(_("There should remain at least one System Manager"))

	def on_trash(self):
		dataent.clear_cache(user=self.name)
		if self.name in STANDARD_USERS:
			throw(_("User {0} cannot be deleted").format(self.name))

		self.a_system_manager_should_exist()

		# disable the user and log him/her out
		self.enabled = 0
		if getattr(dataent.local, "login_manager", None):
			dataent.local.login_manager.logout(user=self.name)

		# delete todos
		dataent.db.sql("""delete from `tabToDo` where owner=%s""", (self.name,))
		dataent.db.sql("""update tabToDo set assigned_by=null where assigned_by=%s""",
			(self.name,))

		# delete events
		dataent.db.sql("""delete from `tabEvent` where owner=%s
			and event_type='Private'""", (self.name,))

		# delete shares
		dataent.db.sql("""delete from `tabDocShare` where user=%s""", self.name)

		# delete messages
		dataent.db.sql("""delete from `tabCommunication`
			where communication_type in ('Chat', 'Notification')
			and reference_doctype='User'
			and (reference_name=%s or owner=%s)""", (self.name, self.name))

		# unlink contact
		dataent.db.sql("""update `tabContact`
			set user=null
			where user=%s""", (self.name))


	def before_rename(self, old_name, new_name, merge=False):
		self.check_demo()
		dataent.clear_cache(user=old_name)
		self.validate_rename(old_name, new_name)

	def validate_rename(self, old_name, new_name):
		# do not allow renaming administrator and guest
		if old_name in STANDARD_USERS:
			throw(_("User {0} cannot be renamed").format(self.name))

		self.validate_email_type(new_name)

	def validate_email_type(self, email):
		from dataent.utils import validate_email_add
		validate_email_add(email.strip(), True)

	def after_rename(self, old_name, new_name, merge=False):
		tables = dataent.db.sql("show tables")
		for tab in tables:
			desc = dataent.db.sql("desc `%s`" % tab[0], as_dict=1)
			has_fields = []
			for d in desc:
				if d.get('Field') in ['owner', 'modified_by']:
					has_fields.append(d.get('Field'))
			for field in has_fields:
				dataent.db.sql("""\
					update `%s` set `%s`=%s
					where `%s`=%s""" % \
					(tab[0], field, '%s', field, '%s'), (new_name, old_name))

		if dataent.db.exists("Chat Profile", old_name):
			dataent.rename_doc("Chat Profile", old_name, new_name, force=True)

		# set email
		dataent.db.sql("""\
			update `tabUser` set email=%s
			where name=%s""", (new_name, new_name))

	def append_roles(self, *roles):
		"""Add roles to user"""
		current_roles = [d.role for d in self.get("roles")]
		for role in roles:
			if role in current_roles:
				continue
			self.append("roles", {"role": role})

	def add_roles(self, *roles):
		"""Add roles to user and save"""
		self.append_roles(*roles)
		self.save()

	def remove_roles(self, *roles):
		existing_roles = dict((d.role, d) for d in self.get("roles"))
		for role in roles:
			if role in existing_roles:
				self.get("roles").remove(existing_roles[role])

		self.save()

	def remove_all_roles_for_guest(self):
		if self.name == "Guest":
			self.set("roles", list(set(d for d in self.get("roles") if d.role == "Guest")))

	def remove_disabled_roles(self):
		disabled_roles = [d.name for d in dataent.get_all("Role", filters={"disabled":1})]
		for role in list(self.get('roles')):
			if role.role in disabled_roles:
				self.get('roles').remove(role)

	def ensure_unique_roles(self):
		exists = []
		for i, d in enumerate(self.get("roles")):
			if (not d.role) or (d.role in exists):
				self.get("roles").remove(d)
			else:
				exists.append(d.role)

	def validate_username(self):
		if not self.username and self.is_new() and self.first_name:
			self.username = dataent.scrub(self.first_name)

		if not self.username:
			return

		# strip space and @
		self.username = self.username.strip(" @")

		if self.username_exists():
			if self.user_type == 'System User':
				dataent.msgprint(_("Username {0} already exists").format(self.username))
				self.suggest_username()

			self.username = ""

	def password_strength_test(self):
		""" test password strength """
		if self.__new_password:
			user_data = (self.first_name, self.middle_name, self.last_name, self.email, self.birth_date)
			result = test_password_strength(self.__new_password, '', None, user_data)
			feedback = result.get("feedback", None)

			if feedback and not feedback.get('password_policy_validation_passed', False):
				handle_password_test_fail(result)

	def suggest_username(self):
		def _check_suggestion(suggestion):
			if self.username != suggestion and not self.username_exists(suggestion):
				return suggestion

			return None

		# @firstname
		username = _check_suggestion(dataent.scrub(self.first_name))

		if not username:
			# @firstname_last_name
			username = _check_suggestion(dataent.scrub("{0} {1}".format(self.first_name, self.last_name or "")))

		if username:
			dataent.msgprint(_("Suggested Username: {0}").format(username))

		return username

	def username_exists(self, username=None):
		return dataent.db.get_value("User", {"username": username or self.username, "name": ("!=", self.name)})

	def get_blocked_modules(self):
		"""Returns list of modules blocked for that user"""
		return [d.module for d in self.block_modules] if self.block_modules else []

	def validate_user_limit(self):
		'''
			Validate if user limit has been reached for System Users
			Checked in 'Validate' event as we don't want welcome email sent if max users are exceeded.
		'''

		if self.user_type == "Website User":
			return

		if not self.enabled:
			# don't validate max users when saving a disabled user
			return

		limits = get_limits()
		if not limits.users:
			# no limits defined
			return

		total_users = get_total_users()
		if self.is_new():
			# get_total_users gets existing users in database
			# a new record isn't inserted yet, so adding 1
			total_users += 1

		if total_users > limits.users:
			dataent.throw(_("Sorry. You have reached the maximum user limit for your subscription. You can either disable an existing user or buy a higher subscription plan."),
				MaxUsersReachedError)

	def validate_user_email_inbox(self):
		""" check if same email account added in User Emails twice """

		email_accounts = [ user_email.email_account for user_email in self.user_emails ]
		if len(email_accounts) != len(set(email_accounts)):
			dataent.throw(_("Email Account added multiple times"))

	def get_social_login_userid(self, provider):
		try:
			for p in self.social_logins:
				if p.provider == provider:
					return p.userid
		except:
			return None

	def set_social_login_userid(self, provider, userid, username=None):
		social_logins = {
			"provider": provider,
			"userid": userid
		}

		if username:
			social_logins["username"] = username

		self.append("social_logins", social_logins)

	def get_restricted_ip_list(self):
		if not self.restrict_ip:
			return

		ip_list = self.restrict_ip.replace(",", "\n").split('\n')
		ip_list = [i.strip() for i in ip_list]

		return ip_list

@dataent.whitelist()
def get_timezones():
	import pytz
	return {
		"timezones": pytz.all_timezones
	}

@dataent.whitelist()
def get_all_roles(arg=None):
	"""return all roles"""
	active_domains = dataent.get_active_domains()

	roles = dataent.get_all("Role", filters={
		"name": ("not in", "Administrator,Guest,All"),
		"disabled": 0
	}, or_filters={
		"ifnull(restrict_to_domain, '')": "",
		"restrict_to_domain": ("in", active_domains)
	}, order_by="name")

	return [ role.get("name") for role in roles ]

@dataent.whitelist()
def get_roles(arg=None):
	"""get roles for a user"""
	return dataent.get_roles(dataent.form_dict['uid'])

@dataent.whitelist()
def get_perm_info(role):
	"""get permission info"""
	from dataent.permissions import get_all_perms
	return get_all_perms(role)

@dataent.whitelist(allow_guest=True)
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
	result = test_password_strength(new_password, key, old_password)
	feedback = result.get("feedback", None)

	if feedback and not feedback.get('password_policy_validation_passed', False):
		handle_password_test_fail(result)

	res = _get_user_for_update_password(key, old_password)
	if res.get('message'):
		return res['message']
	else:
		user = res['user']

	_update_password(user, new_password, logout_all_sessions=int(logout_all_sessions))

	user_doc, redirect_url = reset_user_data(user)

	# get redirect url from cache
	redirect_to = dataent.cache().hget('redirect_after_login', user)
	if redirect_to:
		redirect_url = redirect_to
		dataent.cache().hdel('redirect_after_login', user)

	dataent.local.login_manager.login_as(user)

	if user_doc.user_type == "System User":
		return "/desk"
	else:
		return redirect_url if redirect_url else "/"

@dataent.whitelist(allow_guest=True)
def test_password_strength(new_password, key=None, old_password=None, user_data=[]):
	from dataent.utils.password_strength import test_password_strength as _test_password_strength

	password_policy = dataent.db.get_value("System Settings", None,
		["enable_password_policy", "minimum_password_score"], as_dict=True) or {}

	enable_password_policy = cint(password_policy.get("enable_password_policy", 0))
	minimum_password_score = cint(password_policy.get("minimum_password_score", 0))

	if not enable_password_policy:
		return {}

	if not user_data:
		user_data = dataent.db.get_value('User', dataent.session.user,
			['first_name', 'middle_name', 'last_name', 'email', 'birth_date'])

	if new_password:
		result = _test_password_strength(new_password, user_inputs=user_data)
		password_policy_validation_passed = False

		# score should be greater than 0 and minimum_password_score
		if result.get('score') and result.get('score') >= minimum_password_score:
			password_policy_validation_passed = True

		result['feedback']['password_policy_validation_passed'] = password_policy_validation_passed
		return result

#for login
@dataent.whitelist()
def has_email_account(email):
	return dataent.get_list("Email Account", filters={"email_id": email})

@dataent.whitelist(allow_guest=False)
def get_email_awaiting(user):
	waiting = dataent.db.sql("""select email_account,email_id
		from `tabUser Email`
		where awaiting_password = 1
		and parent = %(user)s""", {"user":user}, as_dict=1)
	if waiting:
		return waiting
	else:
		dataent.db.sql("""update `tabUser Email`
				set awaiting_password =0
				where parent = %(user)s""",{"user":user})
		return False

@dataent.whitelist(allow_guest=False)
def set_email_password(email_account, user, password):
	account = dataent.get_doc("Email Account", email_account)
	if account.awaiting_password:
		account.awaiting_password = 0
		account.password = password
		try:
			account.save(ignore_permissions=True)
		except Exception:
			dataent.db.rollback()
			return False

	return True

def setup_user_email_inbox(email_account, awaiting_password, email_id, enable_outgoing):
	""" setup email inbox for user """
	def add_user_email(user):
		user = dataent.get_doc("User", user)
		row = user.append("user_emails", {})

		row.email_id = email_id
		row.email_account = email_account
		row.awaiting_password = awaiting_password or 0
		row.enable_outgoing = enable_outgoing or 0

		user.save(ignore_permissions=True)

	udpate_user_email_settings = False
	if not all([email_account, email_id]):
		return

	user_names = dataent.db.get_values("User", { "email": email_id }, as_dict=True)
	if not user_names:
		return

	for user in user_names:
		user_name = user.get("name")

		# check if inbox is alreay configured
		user_inbox = dataent.db.get_value("User Email", {
			"email_account": email_account,
			"parent": user_name
		}, ["name"]) or None

		if not user_inbox:
			add_user_email(user_name)
		else:
			# update awaiting password for email account
			udpate_user_email_settings = True

	if udpate_user_email_settings:
		dataent.db.sql("""UPDATE `tabUser Email` SET awaiting_password = %(awaiting_password)s,
			enable_outgoing = %(enable_outgoing)s WHERE email_account = %(email_account)s""", {
				"email_account": email_account,
				"enable_outgoing": enable_outgoing,
				"awaiting_password": awaiting_password or 0
			})
	else:
		users = " and ".join([dataent.bold(user.get("name")) for user in user_names])
		dataent.msgprint(_("Enabled email inbox for user {0}").format(users))

	ask_pass_update()

def remove_user_email_inbox(email_account):
	""" remove user email inbox settings if email account is deleted """
	if not email_account:
		return

	users = dataent.get_all("User Email", filters={
		"email_account": email_account
	}, fields=["parent as name"])

	for user in users:
		doc = dataent.get_doc("User", user.get("name"))
		to_remove = [ row for row in doc.user_emails if row.email_account == email_account ]
		[ doc.remove(row) for row in to_remove ]

		doc.save(ignore_permissions=True)

def ask_pass_update():
	# update the sys defaults as to awaiting users
	from dataent.utils import set_default

	users = dataent.db.sql("""SELECT DISTINCT(parent) as user FROM `tabUser Email`
		WHERE awaiting_password = 1""", as_dict=True)

	password_list = [ user.get("user") for user in users ]
	set_default("email_user_password", u','.join(password_list))

def _get_user_for_update_password(key, old_password):
	# verify old password
	if key:
		user = dataent.db.get_value("User", {"reset_password_key": key})
		if not user:
			return {
				'message': _("Cannot Update: Incorrect / Expired Link.")
			}

	elif old_password:
		# verify old password
		dataent.local.login_manager.check_password(dataent.session.user, old_password)
		user = dataent.session.user

	else:
		return

	return {
		'user': user
	}

def reset_user_data(user):
	user_doc = dataent.get_doc("User", user)
	redirect_url = user_doc.redirect_url
	user_doc.reset_password_key = ''
	user_doc.redirect_url = ''
	user_doc.save(ignore_permissions=True)

	return user_doc, redirect_url

@dataent.whitelist()
def verify_password(password):
	dataent.local.login_manager.check_password(dataent.session.user, password)

@dataent.whitelist(allow_guest=True)
def sign_up(email, full_name, redirect_to):
	if not is_signup_enabled():
		dataent.throw(_('Sign Up is disabled'), title='Not Allowed')

	user = dataent.db.get("User", {"email": email})
	if user:
		if user.disabled:
			return 0, _("Registered but disabled")
		else:
			return 0, _("Already Registered")
	else:
		if dataent.db.sql("""select count(*) from tabUser where
			HOUR(TIMEDIFF(CURRENT_TIMESTAMP, TIMESTAMP(modified)))=1""")[0][0] > 300:

			dataent.respond_as_web_page(_('Temperorily Disabled'),
				_('Too many users signed up recently, so the registration is disabled. Please try back in an hour'),
				http_status_code=429)

		from dataent.utils import random_string
		user = dataent.get_doc({
			"doctype":"User",
			"email": email,
			"first_name": full_name,
			"enabled": 1,
			"new_password": random_string(10),
			"user_type": "Website User"
		})
		user.flags.ignore_permissions = True
		user.insert()

		# set default signup role as per Portal Settings
		default_role = dataent.db.get_value("Portal Settings", None, "default_role")
		if default_role:
			user.add_roles(default_role)

		if redirect_to:
			dataent.cache().hset('redirect_after_login', user.name, redirect_to)

		if user.flags.email_sent:
			return 1, _("Please check your email for verification")
		else:
			return 2, _("Please ask your administrator to verify your sign-up")

@dataent.whitelist(allow_guest=True)
def reset_password(user):
	if user=="Administrator":
		return 'not allowed'

	try:
		user = dataent.get_doc("User", user)
		if not user.enabled:
			return 'disabled'

		user.validate_reset_password()
		user.reset_password(send_email=True)

		return dataent.msgprint(_("Password reset instructions have been sent to your email"))

	except dataent.DoesNotExistError:
		dataent.clear_messages()
		return 'not found'

def user_query(doctype, txt, searchfield, start, page_len, filters):
	from dataent.desk.reportview import get_match_cond

	user_type_condition = "and user_type = 'System User'"
	if filters and filters.get('ignore_user_type'):
		user_type_condition = ''

	txt = "%{}%".format(txt)
	return dataent.db.sql("""select name, concat_ws(' ', first_name, middle_name, last_name)
		from `tabUser`
		where enabled=1
			{user_type_condition}
			and docstatus < 2
			and name not in ({standard_users})
			and ({key} like %(txt)s
				or concat_ws(' ', first_name, middle_name, last_name) like %(txt)s)
			{mcond}
		order by
			case when name like %(txt)s then 0 else 1 end,
			case when concat_ws(' ', first_name, middle_name, last_name) like %(txt)s
				then 0 else 1 end,
			name asc
		limit %(start)s, %(page_len)s""".format(
			user_type_condition = user_type_condition,
			standard_users=", ".join(["'{0}'".format(dataent.db.escape(u)) for u in STANDARD_USERS]),
			key=searchfield, mcond=get_match_cond(doctype)),
			dict(start=start, page_len=page_len, txt=txt))

def get_total_users():
	"""Returns total no. of system users"""
	return dataent.db.sql('''select sum(simultaneous_sessions) from `tabUser`
		where enabled=1 and user_type="System User"
		and name not in ({})'''.format(", ".join(["%s"]*len(STANDARD_USERS))), STANDARD_USERS)[0][0]

def get_system_users(exclude_users=None, limit=None):
	if not exclude_users:
		exclude_users = []
	elif not isinstance(exclude_users, (list, tuple)):
		exclude_users = [exclude_users]

	limit_cond = ''
	if limit:
		limit_cond = 'limit {0}'.format(limit)

	exclude_users += list(STANDARD_USERS)

	system_users = dataent.db.sql_list("""select name from `tabUser`
		where enabled=1 and user_type != 'Website User'
		and name not in ({}) {}""".format(", ".join(["%s"]*len(exclude_users)), limit_cond),
		exclude_users)

	return system_users

def get_active_users():
	"""Returns No. of system users who logged in, in the last 3 days"""
	return dataent.db.sql("""select count(*) from `tabUser`
		where enabled = 1 and user_type != 'Website User'
		and name not in ({})
		and hour(timediff(now(), last_active)) < 72""".format(", ".join(["%s"]*len(STANDARD_USERS))), STANDARD_USERS)[0][0]

def get_website_users():
	"""Returns total no. of website users"""
	return dataent.db.sql("""select count(*) from `tabUser`
		where enabled = 1 and user_type = 'Website User'""")[0][0]

def get_active_website_users():
	"""Returns No. of website users who logged in, in the last 3 days"""
	return dataent.db.sql("""select count(*) from `tabUser`
		where enabled = 1 and user_type = 'Website User'
		and hour(timediff(now(), last_active)) < 72""")[0][0]

def get_permission_query_conditions(user):
	if user=="Administrator":
		return ""

	else:
		return """(`tabUser`.name not in ({standard_users}))""".format(
			standard_users='"' + '", "'.join(STANDARD_USERS) + '"')

def has_permission(doc, user):
	if (user != "Administrator") and (doc.name in STANDARD_USERS):
		# dont allow non Administrator user to view / edit Administrator user
		return False

def notify_admin_access_to_system_manager(login_manager=None):
	if (login_manager
		and login_manager.user == "Administrator"
		and dataent.local.conf.notify_admin_access_to_system_manager):

		site = '<a href="{0}" target="_blank">{0}</a>'.format(dataent.local.request.host_url)
		date_and_time = '<b>{0}</b>'.format(format_datetime(now_datetime(), format_string="medium"))
		ip_address = dataent.local.request_ip

		access_message = _('Administrator accessed {0} on {1} via IP Address {2}.').format(
			site, date_and_time, ip_address)

		dataent.sendmail(
			recipients=get_system_managers(),
			subject=_("Administrator Logged In"),
			template="administrator_logged_in",
			args={'access_message': access_message},
			header=['Access Notification', 'orange']
		)

def extract_mentions(txt):
	"""Find all instances of @name in the string.
	The mentions will be separated by non-word characters or may appear at the start of the string"""
	txt = txt.replace("<div>", "<div> ")
	txt = re.sub(r'(<[a-zA-Z\/][^>]*>)', '', txt)
	return re.findall(r'(?:[^\w\.\-\@]|^)@([\w\.\-\@]*)', txt)

def handle_password_test_fail(result):
	suggestions = result['feedback']['suggestions'][0] if result['feedback']['suggestions'] else ''
	warning = result['feedback']['warning'] if 'warning' in result['feedback'] else ''
	suggestions += "<br>" + _("Hint: Include symbols, numbers and capital letters in the password") + '<br>'
	dataent.throw(' '.join([_('Invalid Password:'), warning, suggestions]))

def update_gravatar(name):
	gravatar = has_gravatar(name)
	if gravatar:
		dataent.db.set_value('User', name, 'user_image', gravatar)

@dataent.whitelist(allow_guest=True)
def send_token_via_sms(tmp_id,phone_no=None,user=None):
	try:
		from dataent.core.doctype.sms_settings.sms_settings import send_request
	except:
		return False

	if not dataent.cache().ttl(tmp_id + '_token'):
		return False
	ss = dataent.get_doc('SMS Settings', 'SMS Settings')
	if not ss.sms_gateway_url:
		return False

	token = dataent.cache().get(tmp_id + '_token')
	args = {ss.message_parameter: 'verification code is {}'.format(token)}

	for d in ss.get("parameters"):
		args[d.parameter] = d.value

	if user:
		user_phone = dataent.db.get_value('User', user, ['phone','mobile_no'], as_dict=1)
		usr_phone = user_phone.mobile_no or user_phone.phone
		if not usr_phone:
			return False
	else:
		if phone_no:
			usr_phone = phone_no
		else:
			return False

	args[ss.receiver_parameter] = usr_phone
	status = send_request(ss.sms_gateway_url, args, use_post=ss.use_post)

	if 200 <= status < 300:
		dataent.cache().delete(tmp_id + '_token')
		return True
	else:
		return False

@dataent.whitelist(allow_guest=True)
def send_token_via_email(tmp_id,token=None):
	import pyotp

	user = dataent.cache().get(tmp_id + '_user')
	count = token or dataent.cache().get(tmp_id + '_token')

	if ((not user) or (user == 'None') or (not count)):
		return False
	user_email = dataent.db.get_value('User',user, 'email')
	if not user_email:
		return False

	otpsecret = dataent.cache().get(tmp_id + '_otp_secret')
	hotp = pyotp.HOTP(otpsecret)

	dataent.sendmail(
		recipients=user_email, sender=None, subject='Verification Code',
		message='<p>Your verification code is {0}</p>'.format(hotp.at(int(count))),
		delayed=False, retry=3)

	return True

@dataent.whitelist(allow_guest=True)
def reset_otp_secret(user):
	otp_issuer = dataent.db.get_value('System Settings', 'System Settings', 'otp_issuer_name')
	user_email = dataent.db.get_value('User',user, 'email')
	if dataent.session.user in ["Administrator", user] :
		dataent.defaults.clear_default(user + '_otplogin')
		dataent.defaults.clear_default(user + '_otpsecret')
		email_args = {
			'recipients':user_email, 'sender':None, 'subject':'OTP Secret Reset - {}'.format(otp_issuer or "Dataent Framework"),
			'message':'<p>Your OTP secret on {} has been reset. If you did not perform this reset and did not request it, please contact your System Administrator immediately.</p>'.format(otp_issuer or "Dataent Framework"),
			'delayed':False,
			'retry':3
		}
		enqueue(method=dataent.sendmail, queue='short', timeout=300, event=None, is_async=True, job_name=None, now=False, **email_args)
		return dataent.msgprint(_("OTP Secret has been reset. Re-registration will be required on next login."))
	else:
		return dataent.throw(_("OTP secret can only be reset by the Administrator."))

def throttle_user_creation():
	if dataent.flags.in_import:
		return

	if dataent.db.get_creation_count('User', 60) > dataent.local.conf.get("throttle_user_limit", 60):
		dataent.throw(_('Throttled'))

@dataent.whitelist()
def get_role_profile(role_profile):
	roles = dataent.get_doc('Role Profile', {'role_profile': role_profile})
	return roles.roles

def update_roles(role_profile):
	users = dataent.get_all('User', filters={'role_profile_name': role_profile})
	role_profile = dataent.get_doc('Role Profile', role_profile)
	roles = [role.role for role in role_profile.roles]
	for d in users:
		user = dataent.get_doc('User', d)
		user.set('roles', [])
		user.add_roles(*roles)

def create_contact(user, ignore_links=False, ignore_mandatory=False):
	if user.name in ["Administrator", "Guest"]: return

	if not dataent.db.get_value("Contact", {"email_id": user.email}):
		dataent.get_doc({
			"doctype": "Contact",
			"first_name": user.first_name,
			"last_name": user.last_name,
			"email_id": user.email,
			"user": user.name,
			"gender": user.gender,
			"phone": user.phone,
			"mobile_no": user.mobile_no
		}).insert(ignore_permissions=True, ignore_links=ignore_links, ignore_mandatory=ignore_mandatory)


@dataent.whitelist()
def generate_keys(user):
	"""
	generate api key and api secret

	:param user: str
	"""
	if "System Manager" in dataent.get_roles():
		user_details = dataent.get_doc("User", user)
		api_secret = dataent.generate_hash(length=15)
		# if api key is not set generate api key
		if not user_details.api_key:
			api_key = dataent.generate_hash(length=15)
			user_details.api_key = api_key
		user_details.api_secret = api_secret
		user_details.save()

		return {"api_secret": api_secret}
	dataent.throw(dataent._("Not Permitted"), dataent.PermissionError)
