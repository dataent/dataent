from __future__ import unicode_literals, print_function
import dataent

def execute():
	for doctype in dataent.get_all("DocType", filters={"issingle": 0}):
		doctype = doctype.name
		if not dataent.db.table_exists(doctype):
			continue

		for column in dataent.db.sql("desc `tab{doctype}`".format(doctype=doctype), as_dict=True):
			fieldname = column["Field"]
			column_type = column["Type"]

			if not column_type.startswith("varchar"):
				continue

			max_length = dataent.db.sql("""select max(char_length(`{fieldname}`)) from `tab{doctype}`"""\
				.format(fieldname=fieldname, doctype=doctype))

			max_length = max_length[0][0] if max_length else None

			if max_length and 140 < max_length <= 255:
				print(
					"setting length of '{fieldname}' in '{doctype}' as {length}".format(
					fieldname=fieldname, doctype=doctype, length=max_length)
				)

				# create property setter for length
				dataent.make_property_setter({
					"doctype": doctype,
					"fieldname": fieldname,
					"property": "length",
					"value": max_length,
					"property_type": "Int"
				})

		dataent.clear_cache(doctype=doctype)
