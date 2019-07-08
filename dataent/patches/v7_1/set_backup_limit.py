from __future__ import unicode_literals
from dataent.utils import cint
import dataent

def execute():
    backup_limit = dataent.db.get_single_value('System Settings', 'backup_limit')
    
    if cint(backup_limit) == 0:
        dataent.db.set_value('System Settings', 'System Settings', 'backup_limit', 3)
