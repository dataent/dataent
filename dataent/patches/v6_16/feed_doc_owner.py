from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doctype("Communication")

	for doctype, name in dataent.db.sql("""select distinct reference_doctype, reference_name
		from `tabCommunication`
		where
			(reference_doctype is not null and reference_doctype != '')
			and (reference_name is not null and reference_name != '')
			and (reference_owner is null or reference_owner = '')
		for update"""):

		owner = dataent.db.get_value(doctype, name, "owner")

		if not owner:
			continue

		dataent.db.sql("""update `tabCommunication`
			set reference_owner=%(owner)s
			where
				reference_doctype=%(doctype)s
				and reference_name=%(name)s
				and (reference_owner is null or reference_owner = '')""".format(doctype=doctype), {
					"doctype": doctype,
					"name": name,
					"owner": owner
				})

		dataent.db.commit()
