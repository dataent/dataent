# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.model.document import Document
from dataent.utils import validate_email_add ,cint
import imaplib,poplib,smtplib

class EmailDomain(Document):
	def autoname(self):
		if self.domain_name:
			self.name = self.domain_name


	def validate(self):
		"""Validate email id and check POP3/IMAP and SMTP connections is enabled."""
		if self.email_id:
			validate_email_add(self.email_id, True)

		if dataent.local.flags.in_patch or dataent.local.flags.in_test:
			return

		if not dataent.local.flags.in_install and not dataent.local.flags.in_patch:
			try:
				if self.use_imap:
					if self.use_ssl:
						test = imaplib.IMAP4_SSL(self.email_server)
					else:
						test = imaplib.IMAP4(self.email_server)

				else:
					if self.use_ssl:
						test = poplib.POP3_SSL(self.email_server)
					else:
						test = poplib.POP3(self.email_server)

			except Exception:
				dataent.throw(_("Incoming email account not correct"))
				return None
			finally:
				try:
					if self.use_imap:
						test.logout()
					else:
						test.quit()
				except Exception:
					pass
			try:
				if self.use_tls and not self.smtp_port:
					self.smtp_port = 587
				sess = smtplib.SMTP((self.smtp_server or "").encode('utf-8'), cint(self.smtp_port) or None)
				sess.quit()
			except Exception:
				dataent.throw(_("Outgoing email account not correct"))
				return None
		return

	def on_update(self):
		"""update all email accounts using this domain"""
		for email_account in dataent.get_all("Email Account",
		filters={"domain": self.name}):

			try:
				email_account = dataent.get_doc("Email Account",
					email_account.name)
				email_account.set("email_server",self.email_server)
				email_account.set("use_imap",self.use_imap)
				email_account.set("use_ssl",self.use_ssl)
				email_account.set("use_tls",self.use_tls)
				email_account.set("attachment_limit",self.attachment_limit)
				email_account.set("smtp_server",self.smtp_server)
				email_account.set("smtp_port",self.smtp_port)
				email_account.save()
			except Exception as e:
				dataent.msgprint(email_account.name)
				dataent.throw(e)
				return None

