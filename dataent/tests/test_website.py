from __future__ import unicode_literals

import dataent, unittest
from werkzeug.wrappers import Request
from werkzeug.test import EnvironBuilder

from dataent.website import render

def set_request(**kwargs):
	builder = EnvironBuilder(**kwargs)
	dataent.local.request = Request(builder.get_environ())

class TestWebsite(unittest.TestCase):

	def test_page_load(self):
		dataent.set_user('Guest')
		set_request(method='POST', path='login')
		response = render.render()

		self.assertEquals(response.status_code, 200)

		html = dataent.safe_decode(response.get_data())

		self.assertTrue('/* login-css */' in html)
		self.assertTrue('// login.js' in html)
		self.assertTrue('<!-- login.html -->' in html)
		dataent.set_user('Administrator')

	def test_redirect(self):
		import dataent.hooks
		dataent.hooks.website_redirects = [
			dict(source=r'/testfrom', target=r'://testto1'),
			dict(source=r'/testfromregex.*', target=r'://testto2'),
			dict(source=r'/testsub/(.*)', target=r'://testto3/\1')
		]
		dataent.cache().delete_key('app_hooks')
		dataent.cache().delete_key('website_redirects')

		set_request(method='GET', path='/testfrom')
		response = render.render()
		self.assertEquals(response.status_code, 301)
		self.assertEquals(response.headers.get('Location'), r'://testto1')

		set_request(method='GET', path='/testfromregex/test')
		response = render.render()
		self.assertEquals(response.status_code, 301)
		self.assertEquals(response.headers.get('Location'), r'://testto2')

		set_request(method='GET', path='/testsub/me')
		response = render.render()
		self.assertEquals(response.status_code, 301)
		self.assertEquals(response.headers.get('Location'), r'://testto3/me')

		set_request(method='GET', path='/test404')
		response = render.render()
		self.assertEquals(response.status_code, 404)

		delattr(dataent.hooks, 'website_redirects')
		dataent.cache().delete_key('app_hooks')

