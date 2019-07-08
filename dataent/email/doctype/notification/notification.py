# -*- coding: utf-8 -*-
# Copyright (c) 2018, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
import json, os
from dataent import _
from dataent.model.document import Document
from dataent.core.doctype.role.role import get_emails_from_role
from dataent.utils import validate_email_add, nowdate, parse_val, is_html
from dataent.utils.jinja import validate_template
from dataent.modules.utils import export_module_json, get_doc_module
from six import string_types
from dataent.integrations.doctype.slack_webhook_url.slack_webhook_url import send_slack_message

# imports - third-party imports
import pymysql
from pymysql.constants import ER

class Notification(Document):
	def onload(self):
		'''load message'''
		if self.is_standard:
			self.message = self.get_template()

	def autoname(self):
		if not self.name:
			self.name = self.subject

	def validate(self):
		validate_template(self.subject)
		validate_template(self.message)

		if self.event in ("Days Before", "Days After") and not self.date_changed:
			dataent.throw(_("Please specify which date field must be checked"))

		if self.event=="Value Change" and not self.value_changed:
			dataent.throw(_("Please specify which value field must be checked"))

		self.validate_forbidden_types()
		self.validate_condition()
		self.validate_standard()
		dataent.cache().hdel('notifications', self.document_type)

	def on_update(self):
		path = export_module_json(self, self.is_standard, self.module)
		if path:
			# js
			if not os.path.exists(path + '.md') and not os.path.exists(path + '.html'):
				with open(path + '.md', 'w') as f:
					f.write(self.message)

			# py
			if not os.path.exists(path + '.py'):
				with open(path + '.py', 'w') as f:
					f.write("""from __future__ import unicode_literals

import dataent

def get_context(context):
	# do your magic here
	pass
""")

	def validate_standard(self):
		if self.is_standard and not dataent.conf.developer_mode:
			dataent.throw(_('Cannot edit Standard Notification. To edit, please disable this and duplicate it'))

	def validate_condition(self):
		temp_doc = dataent.new_doc(self.document_type)
		if self.condition:
			try:
				dataent.safe_eval(self.condition, None, get_context(temp_doc))
			except Exception:
				dataent.throw(_("The Condition '{0}' is invalid").format(self.condition))

	def validate_forbidden_types(self):
		forbidden_document_types = ("Email Queue",)
		if (self.document_type in forbidden_document_types
			or dataent.get_meta(self.document_type).istable):
			# currently notifications don't work on child tables as events are not fired for each record of child table

			dataent.throw(_("Cannot set Notification on Document Type {0}").format(self.document_type))

	def get_documents_for_today(self):
		'''get list of documents that will be triggered today'''
		docs = []

		diff_days = self.days_in_advance
		if self.event=="Days After":
			diff_days = -diff_days

		for name in dataent.db.sql_list("""select name from `tab{0}` where
			DATE(`{1}`) = ADDDATE(DATE(%s), INTERVAL %s DAY)""".format(self.document_type,
				self.date_changed), (nowdate(), diff_days or 0)):

			doc = dataent.get_doc(self.document_type, name)

			if self.condition and not dataent.safe_eval(self.condition, None, get_context(doc)):
				continue

			docs.append(doc)

		return docs

	def send(self, doc):
		'''Build recipients and send Notification'''

		context = get_context(doc)
		context = {"doc": doc, "alert": self, "comments": None}
		if doc.get("_comments"):
			context["comments"] = json.loads(doc.get("_comments"))

		if self.is_standard:
			self.load_standard_properties(context)

		if self.channel == 'Email':
			self.send_an_email(doc, context)

		if self.channel == 'Slack':
			self.send_a_slack_msg(doc, context)

		if self.set_property_after_alert:
			allow_update = True
			if doc.docstatus == 1 and not doc.meta.get_field(self.set_property_after_alert).allow_on_submit:
				allow_update = False

			if allow_update:
				dataent.db.set_value(doc.doctype, doc.name, self.set_property_after_alert,
					self.property_value, update_modified = False)
				doc.set(self.set_property_after_alert, self.property_value)

	def send_an_email(self, doc, context):
		from email.utils import formataddr
		subject = self.subject
		if "{" in subject:
			subject = dataent.render_template(self.subject, context)

		attachments = self.get_attachment(doc)
		recipients, cc, bcc = self.get_list_of_recipients(doc, context)
		sender = None
		if self.sender and self.sender_email:
			sender = formataddr((self.sender, self.sender_email))
		dataent.sendmail(recipients = recipients,
			subject = subject,
			sender = sender,
			cc = cc,
			bcc = bcc,
			message = dataent.render_template(self.message, context),
			reference_doctype = doc.doctype,
			reference_name = doc.name,
			attachments = attachments,
			print_letterhead = ((attachments
				and attachments[0].get('print_letterhead')) or False))

	def send_a_slack_msg(self, doc, context):
			send_slack_message(
				webhook_url=self.slack_webhook_url,
				message=dataent.render_template(self.message, context),
				reference_doctype = doc.doctype,
				reference_name = doc.name)

	def get_list_of_recipients(self, doc, context):
		recipients = []
		cc = []
		bcc = []
		for recipient in self.recipients:
			if recipient.condition:
				if not dataent.safe_eval(recipient.condition, None, context):
					continue
			if recipient.email_by_document_field:
				email_ids_value = doc.get(recipient.email_by_document_field)
				if validate_email_add(email_ids_value):
					email_ids = email_ids_value.replace(",", "\n")
					recipients = recipients + email_ids.split("\n")

				# else:
				# 	print "invalid email"
			if recipient.cc and "{" in recipient.cc:
				recipient.cc = dataent.render_template(recipient.cc, context)

			if recipient.cc:
				recipient.cc = recipient.cc.replace(",", "\n")
				cc = cc + recipient.cc.split("\n")

			if recipient.bcc and "{" in recipient.bcc:
				recipient.bcc = dataent.render_template(recipient.bcc, context)

			if recipient.bcc:
				recipient.bcc = recipient.bcc.replace(",", "\n")
				bcc = bcc + recipient.bcc.split("\n")

			#For sending emails to specified role
			if recipient.email_by_role:
				emails = get_emails_from_role(recipient.email_by_role)

				for email in emails:
					recipients = recipients + email.split("\n")

		if not recipients and not cc and not bcc:
			return None, None, None
		return list(set(recipients)), list(set(cc)), list(set(bcc))

	def get_attachment(self, doc):
		""" check print settings are attach the pdf """
		if not self.attach_print:
			return None

		print_settings = dataent.get_doc("Print Settings", "Print Settings")
		if (doc.docstatus == 0 and not print_settings.allow_print_for_draft) or \
			(doc.docstatus == 2 and not print_settings.allow_print_for_cancelled):

			# ignoring attachment as draft and cancelled documents are not allowed to print
			status = "Draft" if doc.docstatus == 0 else "Cancelled"
			dataent.throw(_("""Not allowed to attach {0} document,
				please enable Allow Print For {0} in Print Settings""".format(status)),
				title=_("Error in Notification"))
		else:
			return [{
				"print_format_attachment": 1,
				"doctype": doc.doctype,
				"name": doc.name,
				"print_format": self.print_format,
				"print_letterhead": print_settings.with_letterhead,
				"lang": dataent.db.get_value('Print Format', self.print_format, 'default_print_language')
					if self.print_format else 'en'
			}]


	def get_template(self):
		module = get_doc_module(self.module, self.doctype, self.name)
		def load_template(extn):
			template = ''
			template_path = os.path.join(os.path.dirname(module.__file__),
				dataent.scrub(self.name) + extn)
			if os.path.exists(template_path):
				with open(template_path, 'r') as f:
					template = f.read()
			return template

		return load_template('.html') or load_template('.md')

	def load_standard_properties(self, context):
		'''load templates and run get_context'''
		module = get_doc_module(self.module, self.doctype, self.name)
		if module:
			if hasattr(module, 'get_context'):
				out = module.get_context(context)
				if out: context.update(out)

		self.message = self.get_template()

		if not is_html(self.message):
			self.message = dataent.utils.md_to_html(self.message)

@dataent.whitelist()
def get_documents_for_today(notification):
	notification = dataent.get_doc('Notification', notification)
	notification.check_permission('read')
	return [d.name for d in notification.get_documents_for_today()]

def trigger_daily_alerts():
	trigger_notifications(None, "daily")

def trigger_notifications(doc, method=None):
	if dataent.flags.in_import or dataent.flags.in_patch:
		# don't send notifications while syncing or patching
		return

	if method == "daily":
		for alert in dataent.db.sql_list("""select name from `tabNotification`
			where event in ('Days Before', 'Days After') and enabled=1"""):
			alert = dataent.get_doc("Notification", alert)
			for doc in alert.get_documents_for_today():
				evaluate_alert(doc, alert, alert.event)
				dataent.db.commit()

def evaluate_alert(doc, alert, event):
	from jinja2 import TemplateError
	try:
		if isinstance(alert, string_types):
			alert = dataent.get_doc("Notification", alert)

		context = get_context(doc)

		if alert.condition:
			if not dataent.safe_eval(alert.condition, None, context):
				return

		if event=="Value Change" and not doc.is_new():
			try:
				db_value = dataent.db.get_value(doc.doctype, doc.name, alert.value_changed)
			except pymysql.InternalError as e:
				if e.args[0]== ER.BAD_FIELD_ERROR:
					alert.db_set('enabled', 0)
					dataent.log_error('Notification {0} has been disabled due to missing field'.format(alert.name))
					return

			db_value = parse_val(db_value)
			if (doc.get(alert.value_changed) == db_value) or \
				(not db_value and not doc.get(alert.value_changed)):

				return # value not changed

		if event != "Value Change" and not doc.is_new():
			# reload the doc for the latest values & comments,
			# except for validate type event.
			doc = dataent.get_doc(doc.doctype, doc.name)
		alert.send(doc)
	except TemplateError:
		dataent.throw(_("Error while evaluating Notification {0}. Please fix your template.").format(alert))
	except Exception as e:
		dataent.log_error(message=dataent.get_traceback(), title=str(e))
		dataent.throw(_("Error in Notification"))

def get_context(doc):
	return {"doc": doc, "nowdate": nowdate, "dataent.utils": dataent.utils}
