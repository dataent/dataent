from __future__ import unicode_literals
import dataent
from dataent.utils import now_datetime

def execute():
	dataent.db.sql('update `tabEmail Queue` set send_after=%s where send_after is null', now_datetime())