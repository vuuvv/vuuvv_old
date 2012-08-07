import time
import unittest

from _socket import error as socket_error

from vuuvv.test import TestCase
from vuuvv.core.engine import Task
from vuuvv.core.connection import Connection

class TestConnection(TestCase):
	def test_connection_refused(self):
		conn = Connection()
		with self.assertRaises(socket_error) as e:
			conn.connect(("localhost", 65535))
		print(e.exception.args[0])

	def test_gaierror(self):
		conn = Connection()
		conn.connect(("adomainthatdoesntexist.asdf", 54321))


if __name__ == "__main__":
	unittest.main()
