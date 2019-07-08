from __future__ import unicode_literals
import dataent

def execute():
	domain_settings = dataent.get_doc('Domain Settings')
	active_domains = [d.domain for d in domain_settings.active_domains]

	for domain_name in ('Education', 'Healthcare', 'Hospitality'):
		if dataent.db.exists('Domain', domain_name) and domain_name not in active_domains:
			domain = dataent.get_doc('Domain', domain_name)
			domain.remove_domain()