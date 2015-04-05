#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='UPnP',
	version='0.1',
	packages=['upnp'],
	package_dir = {'':'src'},
)
