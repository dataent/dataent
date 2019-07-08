from __future__ import unicode_literals
import dataent

def execute():
	dataent.reload_doc("core", "doctype", "domain")
	dataent.reload_doc("core", "doctype", "has_domain")
	active_domains = dataent.get_active_domains()
	all_domains = dataent.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = dataent.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()
