# -*- coding: utf-8 -*-

# Enable once fixed that the server is not started when running. See #199
# from scheduler.base.tests import SchedulerTest

import logging

try:
	from telldus.tests import TelldusTest
except ImportError:
	logging.error('Could not import tests from plugin: telldus')

try:
	from upgrade.tests import HotFixManagerTest
except ImportError:
	logging.error('Could not import tests from plugin: upgrade')
