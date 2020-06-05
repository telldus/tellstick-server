#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
    name='Provisioning',
    version='0.1',
    packages=['provisioning'],
    entry_points={
        'telldus.plugins': ['c = provisioning:Manager [cREQ]'],
    },
    extras_require=dict(cREQ='Base>=0.1'),
)
