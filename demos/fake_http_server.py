import sys
import logging
import time
sys.path.insert(0, "..")

from vuuvv.core.servers import TCPServer
from vuuvv.core.connection import Connection
from vuuvv.core.engine import Engine, Task

resp = b"""HTTP/1.1 200 OK
Server: vuuvv
Content-Type: text/plain
Content-Length: 0
Connection: close
"""

count = 0

class FakeHTTPServer(TCPServer):
	def handle_connection(self, connection, address):
		global count

		data = connection.read_until(b"\r\n\r\n")
		conn = Connection()
		conn.connect(("twitter.com", 80), 0.1)
		conn.close()
		connection.write(resp)
		connection.close()
		count += 1
		if count == 10000:
			sys.exit()

server = FakeHTTPServer()
server.listen(8088)

