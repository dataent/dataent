from __future__ import unicode_literals
import dataent

def execute():
	dataent.db.sql("""update tabDocType set document_type='Document'
		where document_type='Transaction'""")
	dataent.db.sql("""update tabDocType set document_type='Setup'
		where document_type='Master'""")		
