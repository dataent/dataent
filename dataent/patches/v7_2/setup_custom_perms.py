from __future__ import unicode_literals
import dataent
from dataent.permissions import setup_custom_perms
from dataent.core.page.permission_manager.permission_manager import get_standard_permissions
from dataent.utils.reset_doc import setup_perms_for

'''
Copy DocPerm to Custom DocPerm where permissions are set differently
'''

def execute():
	for d in dataent.db.get_all('DocType', dict(istable=0, issingle=0, custom=0)):
		setup_perms_for(d.name)
