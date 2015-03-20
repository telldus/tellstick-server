#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('plugins/lib64/python2.7/site-packages/')

import pkg_resources

if __name__ == '__main__':
	for d in ['Board', 'Base', 'Logger', 'ZWave']:
		dist = pkg_resources.get_distribution(d)
		pkg_resources.working_set.add(dist)
	from base import Application
	from log import Logger
	from zwave.certification import CertificationHelper

	app = Application(run=False)
	app.run(startup=[Logger, CertificationHelper])
