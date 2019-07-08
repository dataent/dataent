# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.utils.scheduler import disable_scheduler, enable_scheduler
from dataent.utils import cint

def execute():
	dataent.reload_doc("core", "doctype", "system_settings")
	if cint(dataent.db.get_global("disable_scheduler")):
		disable_scheduler()
	else:
		enable_scheduler()
