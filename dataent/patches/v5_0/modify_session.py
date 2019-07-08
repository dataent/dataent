from __future__ import unicode_literals
import dataent

def execute():
	if "device" not in dataent.db.get_table_columns("Sessions"):
		dataent.db.sql("alter table tabSessions add column `device` varchar(255) default 'desktop'")
