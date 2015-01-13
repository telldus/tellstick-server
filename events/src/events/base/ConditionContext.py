# -*- coding: utf-8 -*-

from threading import Timer

class ConditionContext(object):
	EVALUATING, DONE = range(2)

	def __init__(self, event, conditions, success, failure):
		super(ConditionContext,self).__init__()
		self.event = event
		self.success = success
		self.failure = failure
		self.conditions = []
		self.state = ConditionContext.EVALUATING
		for i in conditions:
			group = []
			for c in conditions[i].conditions:
				group.append(ConditionsEvaluation(self, conditions[i].conditions[c]))
			self.conditions.append(group)

	def evaluate(self):
		for group in self.conditions:
			success = True
			for condition in group:
				if condition.state == ConditionsEvaluation.UNEVALUATED:
					condition.evaluate()
					return
				elif condition.state == ConditionsEvaluation.FAILED:
					# No need to evaluate more conditions in this group
					success = False
					break
			if success == True:
				# No need to evaluate more conditions
				self.state = ConditionContext.DONE
				self.success()
				return
		self.state = ConditionContext.DONE
		self.failure()

class ConditionsEvaluation(object):
	UNEVALUATED, EVALUATING, SUCCESS, FAILED = range(4)

	def __init__(self, context, condition):
		super(ConditionsEvaluation,self).__init__()
		self.condition = condition
		self.context = context
		self.state = ConditionsEvaluation.UNEVALUATED
		self.timeout = None

	def evaluate(self):
		self.state = ConditionsEvaluation.EVALUATING
		# Start timeout if server doesn't reply
		self.timeout = Timer(30.0, self.__failure)
		self.timeout.start()
		self.condition.validate(success=self.__success, failure=self.__failure)

	def __success(self):
		if self.state != ConditionsEvaluation.EVALUATING:
			return
		if self.timeout != None:
			self.timeout.cancel()
			self.timeout = None
		self.state = ConditionsEvaluation.SUCCESS
		self.context.event.manager.live.pushToWeb('event', 'condition', {
			'event': self.context.event.eventId,
			'condition': self.condition.id,
			'type': 'success'
		})
		self.context.evaluate()

	def __failure(self):
		if self.state != ConditionsEvaluation.EVALUATING:
			return
		if self.timeout != None:
			self.timeout.cancel()
			self.timeout = None
		self.state = ConditionsEvaluation.FAILED
		self.context.event.manager.live.pushToWeb('event', 'condition', {
			'event': self.context.event.eventId,
			'condition': self.condition.id,
			'type': 'failure'
		})
		self.context.evaluate()
