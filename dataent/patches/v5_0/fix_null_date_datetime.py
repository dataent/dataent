from __future__ import unicode_literals
import dataent

def execute():
	for table in dataent.db.get_tables():
		changed = False
		desc = dataent.db.sql("desc `{table}`".format(table=table), as_dict=True)
		for field in desc:
			if field["Type"] == "date":
				dataent.db.sql("""update `{table}` set `{fieldname}`=null where `{fieldname}`='0000-00-00'""".format(
					table=table, fieldname=field["Field"]))
				changed = True

			elif field["Type"] == "datetime(6)":
				dataent.db.sql("""update `{table}` set `{fieldname}`=null where `{fieldname}`='0000-00-00 00:00:00.000000'""".format(
					table=table, fieldname=field["Field"]))
				changed = True

		if changed:
			dataent.db.commit()
