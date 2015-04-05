#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Philips Hue',
	version='0.1',
	packages=['hue'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = hue:Hue [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldusWeb>=0.1'),
	package_data={'hue' : [
		'templates/*.html',
		'htdocs/img/*.jpg',
	]}
)
