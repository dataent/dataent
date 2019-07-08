from __future__ import unicode_literals

# imports - standard imports
import unittest

# imports - module imports
import dataent

# imports - dataent module imports
from dataent.chat.doctype.chat_message import chat_message
from dataent.chat.util import create_test_user

session   = dataent.session
test_user = create_test_user(__name__)

class TestChatMessage(unittest.TestCase):
	def test_send(self):
		# TODO - Write the case once you're done with Chat Room
		# user = test_user
		# chat_message.send(user, room, 'foobar')
		pass
