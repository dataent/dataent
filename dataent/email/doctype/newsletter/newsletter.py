# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import dataent
import dataent.utils
from dataent import throw, _
from dataent.website.website_generator import WebsiteGenerator
from dataent.email.queue import check_email_limit
from dataent.utils.verified_command import get_signed_params, verify_request
from dataent.utils.background_jobs import enqueue
from dataent.utils.scheduler import log
from dataent.email.queue import send
from dataent.email.doctype.email_group.email_group import add_subscribers
from dataent.utils import parse_addr
from dataent.utils import validate_email_add


class Newsletter(WebsiteGenerator):
	def onload(self):
		if self.email_sent:
			self.get("__onload").status_count = dict(dataent.db.sql("""select status, count(name)
				from `tabEmail Queue` where reference_doctype=%s and reference_name=%s
				group by status""", (self.doctype, self.name))) or None

	def validate(self):
		self.route = "newsletters/" + self.name
		if self.send_from:
			validate_email_add(self.send_from, True)

	def test_send(self, doctype="Lead"):
		self.recipients = dataent.utils.split_emails(self.test_email_id)
		self.queue_all()
		dataent.msgprint(_("Scheduled to send to {0}").format(self.test_email_id))

	def send_emails(self):
		"""send emails to leads and customers"""
		if self.email_sent:
			throw(_("Newsletter has already been sent"))

		self.recipients = self.get_recipients()

		if getattr(dataent.local, "is_ajax", False):
			self.validate_send()

			# using default queue with a longer timeout as this isn't a scheduled task
			enqueue(send_newsletter, queue='default', timeout=6000, event='send_newsletter',
				newsletter=self.name)

		else:
			self.queue_all()

		dataent.msgprint(_("Scheduled to send to {0} recipients").format(len(self.recipients)))

		dataent.db.set(self, "email_sent", 1)
		dataent.db.set(self, 'scheduled_to_send', len(self.recipients))

	def queue_all(self):
		if not self.get("recipients"):
			# in case it is called via worker
			self.recipients = self.get_recipients()

		self.validate_send()

		sender = self.send_from or dataent.utils.get_formatted_email(self.owner)

		if not dataent.flags.in_test:
			dataent.db.auto_commit_on_many_writes = True

		attachments = []
		if self.send_attachements:
			files = dataent.get_all("File", fields = ["name"], filters = {"attached_to_doctype": "Newsletter",
				"attached_to_name":self.name}, order_by="creation desc")

			for file in files:
				try:
					# these attachments will be attached on-demand
					# and won't be stored in the message
					attachments.append({"fid": file.name})
				except IOError:
					dataent.throw(_("Unable to find attachment {0}").format(file.name))

		send(recipients = self.recipients, sender = sender,
			subject = self.subject, message = self.message,
			reference_doctype = self.doctype, reference_name = self.name,
			add_unsubscribe_link = self.send_unsubscribe_link, attachments=attachments,
			unsubscribe_method = "/api/method/dataent.email.doctype.newsletter.newsletter.unsubscribe",
			unsubscribe_params = {"name": self.name},
			send_priority = 0, queue_separately=True)

		if not dataent.flags.in_test:
			dataent.db.auto_commit_on_many_writes = False

	def get_recipients(self):
		"""Get recipients from Email Group"""
		recipients_list = []
		for email_group in get_email_groups(self.name):
			for d in dataent.db.get_all("Email Group Member", ["email"],
				{"unsubscribed": 0, "email_group": email_group.email_group}):
					recipients_list.append(d.email)
		return list(set(recipients_list))

	def validate_send(self):
		if self.get("__islocal"):
			throw(_("Please save the Newsletter before sending"))
		check_email_limit(self.recipients)

	def get_context(self, context):
		newsletters = get_newsletter_list("Newsletter", None, None, 0)
		if newsletters:
			newsletter_list = [d.name for d in newsletters]
			if self.name not in newsletter_list:
				dataent.redirect_to_message(_('Permission Error'),
					_("You are not permitted to view the newsletter."))
				dataent.local.flags.redirect_location = dataent.local.response.location
				raise dataent.Redirect
			else:
				context.attachments = get_attachments(self.name)
		context.no_cache = 1
		context.show_sidebar = True


def get_attachments(name):
	return dataent.get_all("File",
			fields=["name", "file_name", "file_url", "is_private"],
			filters = {"attached_to_name": name, "attached_to_doctype": "Newsletter", "is_private":0})


def get_email_groups(name):
	return dataent.db.get_all("Newsletter Email Group", ["email_group"],{"parent":name, "parenttype":"Newsletter"})


@dataent.whitelist(allow_guest=True)
def unsubscribe(email, name):
	if not verify_request():
		return

	primary_action = dataent.utils.get_url() + "/api/method/dataent.email.doctype.newsletter.newsletter.confirmed_unsubscribe"+\
		"?" + get_signed_params({"email": email, "name":name.encode('utf-8')})
	return_confirmation_page(email, name, primary_action)


@dataent.whitelist(allow_guest=True)
def confirmed_unsubscribe(email, name):
	if not verify_request():
		return

	for email_group in get_email_groups(name):
		dataent.db.sql('''update `tabEmail Group Member` set unsubscribed=1 where email=%s and email_group=%s''',(email, email_group.email_group))

	dataent.db.commit()
	return_unsubscribed_page(email, name)

def return_confirmation_page(email, name, primary_action):
	dataent.respond_as_web_page(_("Unsubscribe from Newsletter"),_("Do you want to unsubscribe from this mailing list?"),
		indicator_color="blue", primary_label = _("Unsubscribe"), primary_action=primary_action)

def return_unsubscribed_page(email, name):
	dataent.respond_as_web_page(_("Unsubscribed from Newsletter"),
		_("<b>{0}</b> has been successfully unsubscribed from this mailing list.").format(email, name), indicator_color='green')

def create_lead(email_id):
	"""create a lead if it does not exist"""
	from dataent.model.naming import get_default_naming_series
	full_name, email_id = parse_addr(email_id)
	if dataent.db.get_value("Lead", {"email_id": email_id}):
		return

	lead = dataent.get_doc({
		"doctype": "Lead",
		"email_id": email_id,
		"lead_name": full_name or email_id,
		"status": "Lead",
		"naming_series": get_default_naming_series("Lead"),
		"company": dataent.db.get_default("Company"),
		"source": "Email"
	})
	lead.insert()


@dataent.whitelist(allow_guest=True)
def subscribe(email):
	url = dataent.utils.get_url("/api/method/dataent.email.doctype.newsletter.newsletter.confirm_subscription") +\
		"?" + get_signed_params({"email": email})

	messages = (
		_("Thank you for your interest in subscribing to our updates"),
		_("Please verify your Email Address"),
		url,
		_("Click here to verify")
	)

	content = """
	<p>{0}. {1}.</p>
	<p><a href="{2}">{3}</a></p>
	"""

	dataent.sendmail(email, subject=_("Confirm Your Email"), content=content.format(*messages))

@dataent.whitelist(allow_guest=True)
def confirm_subscription(email):
	if not verify_request():
		return

	if not dataent.db.exists("Email Group", _("Website")):
		dataent.get_doc({
			"doctype": "Email Group",
			"title": _("Website")
		}).insert(ignore_permissions=True)


	dataent.flags.ignore_permissions = True

	add_subscribers(_("Website"), email)
	dataent.db.commit()

	dataent.respond_as_web_page(_("Confirmed"),
		_("{0} has been successfully added to the Email Group.").format(email),
		indicator_color='green')


def send_newsletter(newsletter):
	try:
		doc = dataent.get_doc("Newsletter", newsletter)
		doc.queue_all()

	except:
		dataent.db.rollback()

		# wasn't able to send emails :(
		doc.db_set("email_sent", 0)
		dataent.db.commit()

		log("send_newsletter")

		raise

	else:
		dataent.db.commit()


def get_list_context(context=None):
	context.update({
		"show_sidebar": True,
		"show_search": True,
		'no_breadcrumbs': True,
		"title": _("Newsletter"),
		"get_list": get_newsletter_list,
		"row_template": "email/doctype/newsletter/templates/newsletter_row.html",
	})


def get_newsletter_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by="modified"):
	email_group_list = dataent.db.sql('''select eg.name from `tabEmail Group` eg, `tabEmail Group Member` egm
		where egm.unsubscribed=0 and eg.name=egm.email_group and egm.email = %s''', dataent.session.user)
	if email_group_list:
		return dataent.db.sql('''select n.name, n.subject, n.message, n.modified
			from `tabNewsletter` n, `tabNewsletter Email Group` neg
			where n.name = neg.parent and n.email_sent=1 and n.published=1 and neg.email_group in %s
			order by n.modified desc limit {0}, {1}
			'''.format(limit_start, limit_page_length), [email_group_list], as_dict=1)

