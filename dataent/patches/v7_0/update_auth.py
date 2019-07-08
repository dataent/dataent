from __future__ import unicode_literals
import dataent
from dataent.utils.password import create_auth_table, set_encrypted_password

def execute():
	if '__OldAuth' not in dataent.db.get_tables():
		dataent.db.sql_ddl('''alter table `__Auth` rename `__OldAuth`''')

	create_auth_table()

	# user passwords
	dataent.db.sql('''insert ignore into `__Auth` (doctype, name, fieldname, `password`)
		(select 'User', user, 'password', `password` from `__OldAuth`)''')

	dataent.db.commit()

	# other password fields
	for doctype in dataent.db.sql_list('''select distinct parent from `tabDocField`
		where fieldtype="Password" and parent != "User"'''):

		dataent.reload_doctype(doctype)
		meta = dataent.get_meta(doctype)

		for df in meta.get('fields', {'fieldtype': 'Password'}):
			if meta.issingle:
				password = dataent.db.get_value(doctype, doctype, df.fieldname)
				if password:
					set_encrypted_password(doctype, doctype, password, fieldname=df.fieldname)
					dataent.db.set_value(doctype, doctype, df.fieldname, '*'*len(password))

			else:
				for d in dataent.db.sql('''select name, `{fieldname}` from `tab{doctype}`
					where `{fieldname}` is not null'''.format(fieldname=df.fieldname, doctype=doctype), as_dict=True):

					set_encrypted_password(doctype, d.name, d.get(df.fieldname), fieldname=df.fieldname)

				dataent.db.sql('''update `tab{doctype}` set `{fieldname}`=repeat("*", char_length(`{fieldname}`))'''
					.format(doctype=doctype, fieldname=df.fieldname))

			dataent.db.commit()

	dataent.db.sql_ddl('''drop table `__OldAuth`''')
