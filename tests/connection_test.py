import time
import unittest

from vuuvv.test import TestCase
from vuuvv.core.engine import Task
from vuuvv.core.connection import Connection
from vuuvv.core.exceptions import SocketError, ConnectError, TimeoutError

class TestConnection(TestCase):
	def test_connection_refused(self):
		conn = Connection()
		with self.assertRaises(SocketError) as e:
			conn.connect(("localhost", 1))
		self.assertEqual(e.exception.args[0], 10061)

	def test_connection_timeout(self):
		conn = Connection()
		with self.assertRaises(TimeoutError) as e:
			conn.connect(("skdfl.sdkfj", 54321), 0.01)


	#def test_gaierror(self):
	#	conn = Connection()
	#	conn.connect(("adomainthatdoesntexist.asdf", 54321))

if __name__ == "__main__":
	unittest.main()
