# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent.model.document import Document
from dataent.utils import get_datetime

class FeedbackRequest(Document):
	def autoname(self):
		""" feedback request name in the format Feedback for {doctype} {name} on {datetime}"""

		self.name = "Feedback for {doctype} {docname} on {datetime}".format(
			doctype=self.reference_doctype,
			docname=self.reference_name,
			datetime=get_datetime()
		)

	def before_insert(self):
		from dataent.utils import random_string

		self.key = random_string(32)

@dataent.whitelist(allow_guest=True)
def is_valid_feedback_request(key=None):
	if not key:
		return False

	is_feedback_submitted = dataent.db.get_value("Feedback Request", { "key": key }, "is_feedback_submitted")
	if is_feedback_submitted:
		return False
	else:
		return True

def delete_feedback_request():
	""" clear 100 days old feedback request """
	dataent.db.sql("""delete from `tabFeedback Request` where creation<DATE_SUB(NOW(), INTERVAL 100 DAY)""")