from __future__ import unicode_literals

from unittest import TestCase
from dateutil.relativedelta import relativedelta
from dataent.utils.scheduler import (enqueue_applicable_events, restrict_scheduler_events_if_dormant,
	get_enabled_scheduler_events, disable_scheduler_on_expiry)
from dataent import _dict
from dataent.utils.background_jobs import enqueue
from dataent.utils import now_datetime, today, add_days, add_to_date
from dataent.limits import update_limits, clear_limit

import dataent
import time

def test_timeout():
	'''This function needs to be pickleable'''
	time.sleep(100)

class TestScheduler(TestCase):
	def setUp(self):
		dataent.db.set_global('enabled_scheduler_events', "")
		dataent.flags.ran_schedulers = []

	def test_all_events(self):
		last = now_datetime() - relativedelta(hours=2)
		enqueue_applicable_events(dataent.local.site, now_datetime(), last)
		self.assertTrue("all" in dataent.flags.ran_schedulers)

	def test_enabled_events(self):
		dataent.flags.enabled_events = ["hourly", "hourly_long", "daily", "daily_long",
			"weekly", "weekly_long", "monthly", "monthly_long"]

		# maintain last_event and next_event on the same day
		last_event = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
		next_event = last_event + relativedelta(minutes=30)

		enqueue_applicable_events(dataent.local.site, next_event, last_event)
		self.assertFalse("cron" in dataent.flags.ran_schedulers)

		# maintain last_event and next_event on the same day
		last_event = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
		next_event = last_event + relativedelta(hours=2)

		dataent.flags.ran_schedulers = []
		enqueue_applicable_events(dataent.local.site, next_event, last_event)
		self.assertTrue("all" in dataent.flags.ran_schedulers)
		self.assertTrue("hourly" in dataent.flags.ran_schedulers)

		dataent.flags.enabled_events = None

	def test_enabled_events_day_change(self):

		# use flags instead of globals as this test fails intermittently
		# the root cause has not been identified but the culprit seems cache
		# since cache is mutable, it maybe be changed by a parallel process
		dataent.flags.enabled_events = ["daily", "daily_long", "weekly", "weekly_long",
			"monthly", "monthly_long"]

		# maintain last_event and next_event on different days
		next_event = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
		last_event = next_event - relativedelta(hours=2)

		dataent.flags.ran_schedulers = []
		enqueue_applicable_events(dataent.local.site, next_event, last_event)
		self.assertTrue("all" in dataent.flags.ran_schedulers)
		self.assertFalse("hourly" in dataent.flags.ran_schedulers)

		dataent.flags.enabled_events = None


	def test_restrict_scheduler_events(self):
		dataent.set_user("Administrator")
		dormant_date = add_days(today(), -5)
		dataent.db.sql('update tabUser set last_active=%s', dormant_date)

		restrict_scheduler_events_if_dormant()
		dataent.local.conf = _dict(dataent.get_site_config())

		self.assertFalse("all" in get_enabled_scheduler_events())
		self.assertTrue(dataent.conf.get('dormant', False))

		clear_limit("expiry")
		dataent.local.conf = _dict(dataent.get_site_config())


	def test_disable_scheduler_on_expiry(self):
		update_limits({'expiry': add_to_date(today(), days=-1)})
		dataent.local.conf = _dict(dataent.get_site_config())

		if not dataent.db.exists('User', 'test_scheduler@example.com'):
			user = dataent.new_doc('User')
			user.email = 'test_scheduler@example.com'
			user.first_name = 'Test_scheduler'
			user.save()
			user.add_roles('System Manager')

		dataent.db.commit()
		dataent.set_user("test_scheduler@example.com")

		disable_scheduler_on_expiry()

		ss = dataent.get_doc("System Settings")
		self.assertFalse(ss.enable_scheduler)

		clear_limit("expiry")
		dataent.local.conf = _dict(dataent.get_site_config())


	def test_job_timeout(self):
		job = enqueue(test_timeout, timeout=10)
		count = 5
		while count > 0:
			count -= 1
			time.sleep(5)
			if job.get_status()=='failed':
				break

		self.assertTrue(job.is_failed)

	def tearDown(self):
		dataent.flags.ran_schedulers = []
