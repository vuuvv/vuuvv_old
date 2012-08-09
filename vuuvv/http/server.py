
from vuuvv.core.servers import TCPServer

class HTTPServer(TCPServer):
	def handle_connection(self, connection, address):
		HTTPConnection(connection, address)

class HTTPConnection(object):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		self.parse_headers()

	def parse_headers(self):
		connection = self.connection
		data = connection.read_until(b"\r\n\r\n")

