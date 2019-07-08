# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent

def execute():
        dataent.delete_doc_if_exists("DocType", "User Permission for Page and Report")