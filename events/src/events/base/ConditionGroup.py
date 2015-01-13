# -*- coding: utf-8 -*-

from tellduslive.base import LiveMessage

class ConditionGroup(object):
	def __init__(self):
		super(ConditionGroup,self).__init__()
		self.conditions = {}

	def addCondition(self, condition):
		self.conditions[condition.id] = condition

	def validate(self, success, failure):
		failure()
