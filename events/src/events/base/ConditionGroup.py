# -*- coding: utf-8 -*-

class ConditionGroup(object):
	def __init__(self):
		super(ConditionGroup, self).__init__()
		self.conditions = {}

	def addCondition(self, condition):
		self.conditions[condition.id] = condition

	@staticmethod
	def validate(success, failure):
		del success
		failure()
