from __future__ import unicode_literals
import dataent

def execute():
	duplicateRecords = dataent.db.sql("""select count(name) as `count`, allow, user, for_value
		from `tabUser Permission`
		group by allow, user, for_value
		having count(*) > 1 """, as_dict=1)

	for record in duplicateRecords:
		dataent.db.sql("""delete from `tabUser Permission`
			where allow='{0}' and user='{1}' and for_value='{2}' limit {3}"""
			.format(record.allow, record.user, dataent.db.escape(record.for_value), record.count - 1))
