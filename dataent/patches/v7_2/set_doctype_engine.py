from __future__ import unicode_literals
import dataent

def execute():
	for t in dataent.db.sql('show table status'):
		if t[0].startswith('tab'):
			dataent.db.sql('update tabDocType set engine=%s where name=%s', (t[1], t[0][3:]))