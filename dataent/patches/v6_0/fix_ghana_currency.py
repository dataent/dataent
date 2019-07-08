from __future__ import unicode_literals

def execute():
	from dataent.geo.country_info import get_all
	import dataent.utils.install

	countries = get_all()
	dataent.utils.install.add_country_and_currency("Ghana", dataent._dict(countries["Ghana"]))
