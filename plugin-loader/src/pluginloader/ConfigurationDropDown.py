# -*- coding: utf-8 -*-

from base import ConfigurationValue

class ConfigurationDropDown(ConfigurationValue):
	def __init__(self, options=None, **kwargs):
		super(ConfigurationDropDown, self).__init__(
			'select',
			**kwargs
		)
		self.options = options or {}

	def serialize(self):
		retval = super(ConfigurationDropDown, self).serialize()
		retval['options'] = self.options
		return retval
