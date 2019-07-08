from __future__ import unicode_literals
import dataent

def execute():
	for table in dataent.db.sql_list("show tables"):
		for field in dataent.db.sql("desc `%s`" % table):
			if field[1]=="datetime":
				dataent.db.sql("alter table `%s` change `%s` `%s` datetime(6)" % \
					 (table, field[0], field[0]))
			elif field[1]=="time":
				dataent.db.sql("alter table `%s` change `%s` `%s` time(6)" % \
					 (table, field[0], field[0]))
