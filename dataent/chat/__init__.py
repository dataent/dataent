from __future__ import unicode_literals
import dataent
from   dataent import _

session = dataent.session

def authenticate(user, raise_err = True):
	if session.user == 'Guest':
		if not dataent.db.exists('Chat Token', user):
			if raise_err:
				dataent.throw(_("Sorry, you're not authorized."))
			else:
				return False
		else:
			return True
	else:
		if user != session.user:
			if raise_err:
				dataent.throw(_("Sorry, you're not authorized."))
			else:
				return False
		else:
			return True