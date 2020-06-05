# -*- coding: utf-8 -*-
import logging
import os.path

import yaml
from base import Application, implements, Plugin, SignalManager
from board import Board

_LOGGER = logging.getLogger(__name__)


class Manager(Plugin):
	# implements(ITelldusLiveObserver)

	def __init__(self):
		Application().queue(self.setup)

	def setup(self):
		path = '{}/provisioning.yml'.format(Board.filesPath())
		if not os.path.exists(path):
			# File not yet available.
			return
		with open(path, 'r') as fd:
			data = yaml.safe_load(fd)
		signalManager = SignalManager(self.context)
		late = []
		for func, opts in signalManager.observersForSignal('provisioning'):
			profileName = opts.get('profile', None)
			if not profileName:
				continue
			profile = data.get(profileName, None)
			if not profile:
				continue
			if opts.get('early', False):
				Application().createTask(func, profile)
			else:
				late.append((func, profile))
		for func, profile in late:
			Application().createTask(func, profile)
