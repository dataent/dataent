# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import dataent
import unittest

from dataent.tests.test_website import set_request
from dataent.website.render import render

class TestBlogPost(unittest.TestCase):
	def test_generator_view(self):
		pages = dataent.get_all('Blog Post', fields=['name', 'route'],
			filters={'published': 1, 'route': ('!=', '')}, limit =1)

		set_request(path=pages[0].route)
		response = render()

		self.assertTrue(response.status_code, 200)

		html = response.get_data().decode()
		self.assertTrue('<article class="blog-content" itemscope itemtype="http://schema.org/BlogPosting">' in html)

	def test_generator_not_found(self):
		pages = dataent.get_all('Blog Post', fields=['name', 'route'],
			filters={'published': 0}, limit =1)

		dataent.db.set_value('Blog Post', pages[0].name, 'route', 'test-route-000')

		set_request(path='test-route-000')
		response = render()

		self.assertTrue(response.status_code, 404)
