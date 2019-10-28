#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Telldus Remotesupport',
	version='0.1',
	packages=['remotesupport'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.plugins': ['c = remotesupport:RemoteSupport [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldusLive>=0.1'),
	package_data={'remotesupport' : [
		'id_rsa'
	]}
)
