#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='TelldusLive',
	version='0.1',
	packages=find_packages('src'),
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = tellduslive.base:TelldusLive [cREQ]']
	},
	extras_require = dict(cREQ = "Base>=0.1")
)
