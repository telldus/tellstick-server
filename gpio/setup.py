#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='GPIO',
	version='0.1',
	packages=['gpio'],
	package_dir = {'':'src'},
	extras_require = dict(cREQ = 'Base>=0.1'),
)
