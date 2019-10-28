#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name='Upgrade',
	version='0.1',
	packages=['upgrade'],
	extras_require={
		'upgrade': ['Base>=0.1'],
	}
)
