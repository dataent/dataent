#!/usr/bin/env python2.7

# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import os
import dataent
dataent.connect(site=os.environ.get("site"))