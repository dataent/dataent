from __future__ import unicode_literals
import json
import dataent
import dataent.defaults
from dataent.desk.like import _toggle_like
from six import string_types

def execute():
	for user in dataent.get_all("User"):
		username = user["name"]
		bookmarks = dataent.db.get_default("_bookmarks", username)

		if not bookmarks:
			continue

		if isinstance(bookmarks, string_types):
			bookmarks = json.loads(bookmarks)

		for opts in bookmarks:
			route = (opts.get("route") or "").strip("#/ ")

			if route and route.startswith("Form"):
				try:
					view, doctype, docname = opts["route"].split("/")
				except ValueError:
					continue

				if dataent.db.exists(doctype, docname):
					if (doctype=="DocType"
						or int(dataent.db.get_value("DocType", doctype, "issingle") or 0)
						or not dataent.db.table_exists(doctype)):
						continue
					_toggle_like(doctype, docname, add="Yes", user=username)
