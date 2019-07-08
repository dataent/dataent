# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent
from dataent.installer import make_site_dirs

def execute():
	make_site_dirs()
	if dataent.local.conf.backup_path and dataent.local.conf.backup_path.startswith("public"):
		raise Exception("Backups path in conf set to public directory")
