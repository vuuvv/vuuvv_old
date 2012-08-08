import socket
from functools import partial

from .engine import Engine, Task
from .connection import wait_accept

class TCPServer(object):
	def __init__(self, engine=None):
		self.engine = engine or Engine.instance()
		self._sockets = {}

	def stop(self):
		for fd, sock in self._sockets.iteritems():
			self.engine.kill(fd, force_kill_task=True)
			sock.close()

	def listen(self, port, address=""):
		Task(partial(self._listen, port, address)).start()

	def _listen(self, port, address=""):
		sockets = self.bind_sockets(port, address=address)
		self.start_listen_tasks(sockets)

	def handle_connection(self, connection, address):
		raise NotImplementedError()

	def start_listen_tasks(self, sockets):
		for sock in sockets:
			fd = sock.fileno()
			self._sockets[fd] = sock
			Task(partial(wait_accept, sock, self.handle_connection, self.engine)).start()

	def bind_sockets(self, port, address=None, family=socket.AF_UNSPEC, backlog=120):
		sockets = []
		if address == "":
			address = None
		flags = socket.AI_PASSIVE
		if hasattr(socket, "AI_ADDRCONFIG"):
			flags |= socket.AI_ADDRCONFIG

		for res in socket.getaddrinfo(address, port, family, socket.SOCK_STREAM,
				0, flags):
			af, socktype, proto, canonname, sockaddr = res
			sock = socket.socket(af, socktype, proto)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			if af == socket.AF_INET6:
				if hasattr(socket, "IPROTO_IPV6"):
					sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
			sock.setblocking(False)
			sock.bind(sockaddr)
			sock.listen(backlog)
			sockets.append(sock)

		return sockets


