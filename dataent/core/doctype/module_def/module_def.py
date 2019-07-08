# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import dataent, os

from dataent.model.document import Document

class ModuleDef(Document):
	def on_update(self):
		"""If in `developer_mode`, create folder for module and
			add in `modules.txt` of app if missing."""
		dataent.clear_cache()
		if dataent.conf.get("developer_mode"):
			self.create_modules_folder()
			self.add_to_modules_txt()

	def create_modules_folder(self):
		"""Creates a folder `[app]/[module]` and adds `__init__.py`"""
		module_path = dataent.get_app_path(self.app_name, self.name)
		if not os.path.exists(module_path):
			os.mkdir(module_path)
			with open(os.path.join(module_path, "__init__.py"), "w") as f:
				f.write("")

	def add_to_modules_txt(self):
		"""Adds to `[app]/modules.txt`"""
		modules = None
		if not dataent.local.module_app.get(dataent.scrub(self.name)):
			with open(dataent.get_app_path(self.app_name, "modules.txt"), "r") as f:
				content = f.read()
				if not self.name in content.splitlines():
					modules = list(filter(None, content.splitlines()))
					modules.append(self.name)

			if modules:
				with open(dataent.get_app_path(self.app_name, "modules.txt"), "w") as f:
					f.write("\n".join(modules))

				dataent.clear_cache()
				dataent.setup_module_map()
