from time import time
import sys

from greenlet import greenlet

class TimeoutException(Exception):
	pass

class Task(greenlet):
	__slots__ = "func", "last_yield"

	def __init__(self, func, parent=None):
		self.func = func
		super(Task, self).__init__(self._run, parent)

	def process(self, *args, **kwargs):
		self.switch(*args, **kwargs)

	def timeout(self):
		self.throw(TimeoutException)

	def kill(self, exception=greenlet.GreenletExit):
		self.throw(exception)

	def _run(self, *args, **kwargs):
		try:
			self.func(*args, **kwargs)
		except greenlet.GreenletExit:
			return
		except TimeoutException:
			logging.warning('This task is time out')
		except Exception:
			exc = sys.exc_info()
			self.parent.throw(*exc)

