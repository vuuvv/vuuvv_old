import time
import unittest

from _socket import error as socket_error

from vuuvv.test import TestCase
from vuuvv.core.engine import Task
from vuuvv.core.connection import Connection

class TestConnection(unittest.TestCase):
	#def test_connection_refused(self):
	#	port = 999999
	#	conn = Connection()
	#	with self.assertRaises(socket_error):
	#		conn.connect(("localhost", 65535))
	def test_a(self):
		pass

	def test_b(self):
		pass

if __name__ == "__main__":
	import pdb;pdb.set_trace()
	unittest.main()
