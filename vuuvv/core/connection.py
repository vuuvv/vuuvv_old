from socket import socket, AF_INET, SOCK_STREAM
from errno import EINPROGRESS, EWOULDBLOCK

from .engine import Engine, ERROR

class Connection(object):
	def __init__(self, socket, engine=None, max_buffer_size=104857600,
			read_chunk_size=4096):
		self.socket = socket
		self.socket.setblocking(False)
		self.engine = engine or Engine.instance()
		self.max_buffer_size = max_buffer_size
		self.read_chunk_size = read_chunk_size
		self.error = None
		self._io_status = None

	def close(self):
		sock = self.socket
		if sock is not None:
			socket.close()
			self.socket = None

	def connect(self, address):
		try:
			self.socket.connect(address)
		except socket.error as e:
			if e.args[0] not in (EINPROGRESS, EWOULDBLOCK):
				logging.warning("Connect error on fd %d: %s",
					self.socket.fileno(), e)
				self.close()
				return

	def _set_io_status(self, status):
		sock = self.socket
		if sock is None:
			return
		if self._io_status is None:
			status = ERROR | status
			self.engine.add_io(sock.fileno()

