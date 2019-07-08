from __future__ import print_function, unicode_literals
from dataent.utils.selenium_testdriver import TestDriver
import unittest, os, dataent, time

class TestTestRunner(unittest.TestCase):
	def test_test_runner(self):
		if dataent.flags.run_setup_wizard_ui_test:
			for setup_wizard_test in dataent.get_hooks("setup_wizard_test"):
				passed = dataent.get_attr(setup_wizard_test)()
				self.assertTrue(passed)
			return

		driver = TestDriver()
		dataent.db.set_default('in_selenium', '1')
		driver.login()
		for test in get_tests():
			if test.startswith('#'):
				continue

			timeout = 60
			passed = False
			if '#' in test:
				test, comment = test.split('#')
				test = test.strip()
				if comment.strip()=='long':
					timeout = 300

			print('Running {0}...'.format(test))

			dataent.db.set_value('Test Runner', None, 'module_path', test)
			dataent.db.commit()
			driver.refresh()
			driver.set_route('Form', 'Test Runner')
			try:
				driver.click_primary_action()
				driver.wait_for('#dataent-qunit-done', timeout=timeout)
				console = driver.get_console()
				passed  = 'Tests Passed' in console
			finally:
				console = driver.get_console()
				passed  = 'Test Passed' in console
				if dataent.flags.tests_verbose or not passed:
					for line in console:
						print(line)
					print('-' * 40)
				else:
					self.assertTrue(passed)
				time.sleep(1)
		dataent.db.set_default('in_selenium', None)
		driver.close()

def get_tests():
	'''Get tests base on flag'''
	dataent.db.set_value('Test Runner', None, 'app', dataent.flags.ui_test_app or '')

	if dataent.flags.ui_test_list:
		# list of tests
		return get_tests_for(test_list=dataent.flags.ui_test_list)
	elif dataent.flags.ui_test_path:
		# specific test
		return (dataent.flags.ui_test_path,)
	elif dataent.flags.ui_test_app:
		# specific app
		return get_tests_for(dataent.flags.ui_test_app)
	else:
		# all apps
		tests = []
		for app in dataent.get_installed_apps():
			tests.extend(get_tests_for(app))
		return tests

def get_tests_for(app=None, test_list=None):
	tests = []
	if test_list:
		# Get all tests from a particular txt file
		app, test_list = test_list.split(os.path.sep, 1)
		tests_path = dataent.get_app_path(app, test_list)
	else:
		# Get all tests for a particular app
		tests_path = dataent.get_app_path(app, 'tests', 'ui', 'tests.txt')
	if os.path.exists(tests_path):
		with open(tests_path, 'r') as fileobj:
			tests = fileobj.read().strip().splitlines()
	return tests
