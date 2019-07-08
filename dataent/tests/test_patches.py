from __future__ import unicode_literals
import unittest, dataent
from dataent.modules import patch_handler

class TestPatches(unittest.TestCase):
	def test_patch_module_names(self):
		dataent.flags.final_patches = []
		dataent.flags.in_install = True
		for patchmodule in patch_handler.get_all_patches():
			if patchmodule.startswith("execute:"):
				pass
			else:
				if patchmodule.startswith("finally:"):
					patchmodule = patchmodule.split('finally:')[-1]
				self.assertTrue(dataent.get_attr(patchmodule.split()[0] + ".execute"))

		dataent.flags.in_install = False
