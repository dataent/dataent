from __future__ import unicode_literals
import dataent
from dataent.model.db_schema import add_column

def execute():
	dataent.db.sql("""update `tabSingles` set field='_liked_by' where field='_starred_by'""")
	dataent.db.commit()

	for table in dataent.db.get_tables():
		columns = [r[0] for r in dataent.db.sql("DESC `{0}`".format(table))]
		if "_starred_by" in columns and '_liked_by' not in columns:
			dataent.db.sql_ddl("""alter table `{0}` change `_starred_by` `_liked_by` Text """.format(table))

	if not dataent.db.has_column("Communication", "_liked_by"):
		add_column("Communication", "_liked_by", "Text")
