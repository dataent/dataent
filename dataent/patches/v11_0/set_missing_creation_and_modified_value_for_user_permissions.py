import dataent

def execute():
	dataent.db.sql('''UPDATE `tabUser Permission`
		SET `modified`=NOW(), `creation`=NOW()
		WHERE `creation` IS NULL''')