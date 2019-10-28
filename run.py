#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pkg_resources

if __name__ == "__main__":
	paths = ['plugins', '/usr/lib/telldus/plugins']

	distributions, errors =  pkg_resources.working_set.find_plugins(pkg_resources.Environment(paths))
	for dist in distributions:
		if dist not in pkg_resources.working_set:
			print(f"Loading plugin {dist}")
			try:
				pkg_resources.working_set.add(dist)
			except Exception as e:
				print(f"Could not load {dist} {e}")
	for entry in pkg_resources.working_set.iter_entry_points('telldus.main'):
		moduleClass = entry.load()
		m = moduleClass()
		# telldus.main is blocking. Only load one
		break
