# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals
import dataent
from dataent.website.utils import get_full_index

def get_context(context):
	context.full_index = get_full_index()
