from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "docperm")
	
	# delete same as cancel (map old permissions)
	dataent.db.sql("""update tabDocPerm set `delete`=ifnull(`cancel`,0)""")
	
	# can't cancel if can't submit
	dataent.db.sql("""update tabDocPerm set `cancel`=0 where ifnull(`submit`,0)=0""")
	
	dataent.clear_cache()