import sys
import logging
sys.path.insert(0, "..")

from vuuvv.core.servers import TCPServer

class EchoServer(TCPServer):
	def handle_connection(self, connection, address):
		try:
			while True:
				data = connection.read_until(b"\r\n")
				if data == "quit\r\n":
					return
				if data == "shutdown\r\n":
					self.close()
				connection.write(data)
		except SocketClosedUnexcepted as e:
			logging.info("Connection closed")


server = EchoServer()
server.listen(8088)
