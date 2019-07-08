from __future__ import unicode_literals
import dataent

def execute():
	domain_settings = dataent.get_doc('Domain Settings')
	active_domains = [d.domain for d in domain_settings.active_domains]
	try:
		for d in ('Education', 'Healthcare', 'Hospitality'):
			if d in active_domains and dataent.db.exists('Domain', d):
				domain = dataent.get_doc('Domain', d)
				domain.setup_domain()
	except dataent.LinkValidationError:
		pass
