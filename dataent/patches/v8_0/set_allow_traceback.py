from __future__ import unicode_literals
import dataent

def execute():
    dataent.reload_doc('core', 'doctype', 'system_settings')
    dataent.db.sql("update `tabSystem Settings` set allow_error_traceback=1")
