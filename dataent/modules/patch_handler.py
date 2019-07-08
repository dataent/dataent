# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function
"""
	Execute Patch Files

	To run directly

	python lib/wnf.py patch patch1, patch2 etc
	python lib/wnf.py patch -f patch1, patch2 etc

	where patch1, patch2 is module name
"""
import dataent, dataent.permissions, time

# for patches
import os

class PatchError(Exception): pass

def run_all():
	"""run all pending patches"""
	executed = [p[0] for p in dataent.db.sql("""select patch from `tabPatch Log`""")]

	dataent.flags.final_patches = []
	for patch in get_all_patches():
		if patch and (patch not in executed):
			if not run_single(patchmodule = patch):
				log(patch + ': failed: STOPPED')
				raise PatchError(patch)

	# patches to be run in the end
	for patch in dataent.flags.final_patches:
		patch = patch.replace('finally:', '')
		if not run_single(patchmodule = patch):
			log(patch + ': failed: STOPPED')
			raise PatchError(patch)

def get_all_patches():
	patches = []
	for app in dataent.get_installed_apps():
		if app == "shopping_cart":
			continue
		# 3-to-4 fix
		if app=="webnotes":
			app="dataent"
		patches.extend(dataent.get_file_items(dataent.get_pymodule_path(app, "patches.txt")))

	return patches

def reload_doc(args):
	import dataent.modules
	run_single(method = dataent.modules.reload_doc, methodargs = args)

def run_single(patchmodule=None, method=None, methodargs=None, force=False):
	from dataent import conf

	# don't write txt files
	conf.developer_mode = 0

	if force or method or not executed(patchmodule):
		return execute_patch(patchmodule, method, methodargs)
	else:
		return True

def execute_patch(patchmodule, method=None, methodargs=None):
	"""execute the patch"""
	block_user(True)
	dataent.db.begin()
	start_time = time.time()
	try:
		log('Executing {patch} in {site} ({db})'.format(patch=patchmodule or str(methodargs),
			site=dataent.local.site, db=dataent.db.cur_db_name))
		if patchmodule:
			if patchmodule.startswith("finally:"):
				# run run patch at the end
				dataent.flags.final_patches.append(patchmodule)
			else:
				if patchmodule.startswith("execute:"):
					exec(patchmodule.split("execute:")[1],globals())
				else:
					dataent.get_attr(patchmodule.split()[0] + ".execute")()
				update_patch_log(patchmodule)
		elif method:
			method(**methodargs)

	except Exception:
		dataent.db.rollback()
		raise

	else:
		dataent.db.commit()
		end_time = time.time()
		block_user(False)
		log('Success: Done in {time}s'.format(time = round(end_time - start_time, 3)))

	return True

def update_patch_log(patchmodule):
	"""update patch_file in patch log"""
	dataent.get_doc({"doctype": "Patch Log", "patch": patchmodule}).insert(ignore_permissions=True)

def executed(patchmodule):
	"""return True if is executed"""
	if patchmodule.startswith('finally:'):
		# patches are saved without the finally: tag
		patchmodule = patchmodule.replace('finally:', '')
	done = dataent.db.get_value("Patch Log", {"patch": patchmodule})
	# if done:
	# 	print "Patch %s already executed in %s" % (patchmodule, dataent.db.cur_db_name)
	return done

def block_user(block):
	"""stop/start execution till patch is run"""
	dataent.local.flags.in_patch = block
	dataent.db.begin()
	msg = "Patches are being executed in the system. Please try again in a few moments."
	dataent.db.set_global('__session_status', block and 'stop' or None)
	dataent.db.set_global('__session_status_message', block and msg or None)
	dataent.db.commit()

def check_session_stopped():
	if dataent.db.get_global("__session_status")=='stop':
		dataent.msgprint(dataent.db.get_global("__session_status_message"))
		raise dataent.SessionStopped('Session Stopped')

def log(msg):
	print (msg)
