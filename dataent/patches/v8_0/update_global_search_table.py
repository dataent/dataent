from __future__ import unicode_literals
import dataent

def execute():
	if not 'published' in dataent.db.get_db_table_columns('__global_search'):
		dataent.db.sql('''alter table __global_search
			add column `title` varchar(140)''')

		dataent.db.sql('''alter table __global_search
			add column `route` varchar(140)''')

		dataent.db.sql('''alter table __global_search
			add column `published` int(1) not null default 0''')
