# -*- coding: utf-8 -*-

from base import ConfigurationValue

class ConfigurationReactComponent(ConfigurationValue):
	def __init__(self, component, **kwargs):
		super(ConfigurationReactComponent,self).__init__('reactcomponent', **kwargs)
		self.component = component

	def serialize(self):
		retval = super(ConfigurationReactComponent,self).serialize()
		retval['component'] = self.component
		return retval
