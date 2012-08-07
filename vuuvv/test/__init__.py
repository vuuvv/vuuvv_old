import unittest
import functools

from vuuvv.core.engine import Engine, Task

class TestCase(unittest.TestCase):
	def _wrap_run(self, result=None):
		super(TestCase, self).__call__(result)
		Engine.instance().stop()

	def __call__(self, result=None):
		Task(functools.partial(self._wrap_run, result)).start()

	def assertSocketErrno(self, error, excepted):
		if not isinstance(error, socket_error):
			raise RuntimeError("Exception should be a socket.error")


