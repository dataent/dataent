from __future__ import unicode_literals
import dataent

def execute():
	dataent.db.sql("""delete from `__global_search` where doctype='Static Web Page'""");