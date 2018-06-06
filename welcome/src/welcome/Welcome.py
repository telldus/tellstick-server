# -*- coding: utf-8 -*-


from base import Plugin, implements
from telldus.web import IWebReactHandler

class Welcome(Plugin):
	implements(IWebReactHandler)

	@staticmethod
	def getReactComponents():
		return {
			'welcome': {
				'title': 'Welcome',
				'script': 'welcome/welcome.js',
				'tags': ['menu'],
			}
		}