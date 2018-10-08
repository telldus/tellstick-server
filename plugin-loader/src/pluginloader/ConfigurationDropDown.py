# -*- coding: utf-8 -*-

from telldus.web import ConfigurationReactComponent

class ConfigurationDropDown(ConfigurationReactComponent):
	def __init__(self, menuList, selected=None, **kwargs):
		super(ConfigurationDropDown, self).__init__(
			'plugins/dropdown',
			defaultValue={
				"selected": selected,
				"list":menuList
			},
			**kwargs
		)
		self.menuList = menuList or {}
		self.selected = selected
