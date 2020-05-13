#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
    name='Discovery',
    version='0.1',
    packages=['discovery'],
    entry_points={
        'telldus.startup': ['c = discovery:Listener [cREQ]'],
    },
    extras_require=dict(cREQ='Base>=0.1'),
)
