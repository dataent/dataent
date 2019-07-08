from __future__ import unicode_literals
import dataent
from dataent.installer import check_if_ready_for_barracuda
from dataent.model.meta import trim_tables

def execute():
	check_if_ready_for_barracuda()

	for table in dataent.db.get_tables():
		dataent.db.sql_ddl("""alter table `{0}` ENGINE=InnoDB ROW_FORMAT=COMPRESSED""".format(table))
		try:
			dataent.db.sql_ddl("""alter table `{0}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""".format(table))
		except:
			# if row size gets too large, let it be old charset!
			pass

