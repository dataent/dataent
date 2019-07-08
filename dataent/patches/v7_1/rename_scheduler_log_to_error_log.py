from __future__ import unicode_literals
import dataent

def execute():
	if not 'tabError Log' in dataent.db.get_tables():
		dataent.rename_doc('DocType', 'Scheduler Log', 'Error Log')
		dataent.db.sql("""delete from `tabError Log` where datediff(curdate(), creation) > 30""")
		dataent.db.commit()
		dataent.db.sql('alter table `tabError Log` change column name name varchar(140)')
		dataent.db.sql('alter table `tabError Log` change column parent parent varchar(140)')
		dataent.db.sql('alter table `tabError Log` engine=MyISAM')
