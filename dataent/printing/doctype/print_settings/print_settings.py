# -*- coding: utf-8 -*-
# Copyright (c) 2018, Dataent Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.utils import cint

from dataent.model.document import Document

class PrintSettings(Document):
	def on_update(self):
		dataent.clear_cache()

	@dataent.whitelist()
	def get_printers(self,ip="localhost",port=631):
		printer_list = []
		try:
			import cups
		except ImportError:
			dataent.throw(_("You need to install pycups to use this feature!"))
			return
		try:
			cups.setServer(self.server_ip)
			cups.setPort(self.port)
			conn = cups.Connection()
			printers = conn.getPrinters()
			printer_list = printers.keys()
		except RuntimeError:
			dataent.throw(_("Failed to connect to server"))
		except ValidationError:
			dataent.throw(_("Failed to connect to server"))
		return printer_list

@dataent.whitelist()
def is_print_server_enabled():
	if not hasattr(dataent.local, 'enable_print_server'):
		dataent.local.enable_print_server = cint(dataent.db.get_single_value('Print Settings',
			'enable_print_server'))

	return dataent.local.enable_print_server
