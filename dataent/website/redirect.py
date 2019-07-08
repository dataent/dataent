from __future__ import unicode_literals

import re, dataent

def resolve_redirect(path):
	'''
	Resolve redirects from hooks

	Example:

		website_redirect = [
			# absolute location
			{"source": "/from", "target": "https://mysite/from"},

			# relative location
			{"source": "/from", "target": "/main"},

			# use regex
			{"source": r"/from/(.*)", "target": r"/main/\1"}
			# use r as a string prefix if you use regex groups or want to escape any string literal
		]
	'''
	redirects = dataent.get_hooks('website_redirects')
	if not redirects: return

	redirect_to = dataent.cache().hget('website_redirects', path)

	if redirect_to:
		dataent.flags.redirect_location = redirect_to
		raise dataent.Redirect

	for rule in redirects:
		pattern = rule['source'].strip('/ ') + '$'
		if re.match(pattern, path):
			redirect_to = re.sub(pattern, rule['target'], path)
			dataent.flags.redirect_location = redirect_to
			dataent.cache().hset('website_redirects', path, redirect_to)
			raise dataent.Redirect

