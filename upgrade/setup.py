#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='Upgrade',
	version='0.1',
	packages=find_packages('src'),
	package_dir={'':'src'},
	entry_points={ \
		'telldus.startup': ['c = upgrade:UpgradeManager [cREQ]']
	},
	extras_require={
		'upgrade': ['Base>=0.1'],
	}
)
