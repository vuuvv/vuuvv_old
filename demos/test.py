import select
import errno
import logging

import greenlet

class Engine(object):
	_EPOLLIN = 0x001
	_EPOLLPRI = 0x002
	_EPOLLOUT = 0x004
	_EPOLLERR = 0x008
	_EPOLLHUP = 0x010
	_EPOLLRDHUP = 0x2000
	_EPOLLONESHOT = (1 << 30)
	_EPOLLET = (1 << 31)

	NONE = 0
	READ = _EPOLLIN
	WRITE = _EPOLLOUT
	ERROR = _EPOLLERR | _EPOLLHUP

	def __init__(self, impl=None):
		self._impl = impl or _poll()
		self._handlers = {}
		self._events = {}

		self.main_task = greenlet.greenlet(self._start)

	def add_handler(self, fd, handler, events):
		self._handlers[fd] = greenlet.greenlet(handler, self.main_task)
		self._impl.register(fd, events | self.ERROR)

	def remove_handler(self, fd):
		self._handlers.pop(fd, None)
		self._events.pop(fd, None)
		try:
			self._impl.unregister(fd)
		except (OSError, IOError):
			logging.debug("Error deleting fd from IOLoop", exec_info=True)

	def _start(self):
		while True:
			poll_timeout = 3600.0
			event_pairs = self._impl.poll(poll_timeout)

			# protected from remove_handler
			self._events.update(event_pairs)
			while self._events:
				fd, events = self._events.popitem()
				self._handlers[fd].switch(fd, events)

	def start(self):
		self.main_task.switch()

class _Select(object):
	def __init__(self):
		self.read_fds = set()
		self.write_fds = set()
		self.error_fds = set()
		self.fd_sets = (self.read_fds, self.write_fds, self.error_fds)

	def colse(self):
		pass

	def register(self, fd, events):
		if events & Engine.READ:
			self.read_fds.add(fd)
		if events & Engine.WRITE:
			self.write_fds.add(fd)
		if events & Engine.ERROR:
			self.error_fds.add(fd)
			self.read_fds.add(fd)

	def modify(self, fd, events):
		self.unregister(fd)
		self.register(fd, events)

	def unregister(self, fd):
		self.read_fds.discard(fd)
		self.write_fds.discard(fd)
		self.error_fds.discard(fd)

	def poll(self, timeout):
		readable, writeable, errors = select.select(
			self.read_fds, self.write_fds, self.error_fds, timeout)
		events = {}
		for fd in readable:
			events[fd] = events.get(fd, 0) | Engine.READ
		for fd in writeable:
			events[fd] = events.get(fd, 0) | Engine.WRITE
		for fd in errors:
			events[fd] = events.get(fd, 0) | Engine.ERROR
		return events.items()

_poll = _Select

def accept(sock):
	while True:
		parent = greenlet.getcurrent().parent
		parent.switch()
		connection, address = sock.accept()
		print(connection)

if __name__ == '__main__':
	import functools
	import socket

	def cb(sock, fd, events):
		while True:
			connection, address = sock.accept()
			print(fd, events, connection, address)
			connection.send(b"Hello")
			parent = greenlet.getcurrent().parent
			fd, events = parent.switch()

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setblocking(0)
	sock.bind(("localhost", 8888))
	sock.listen(128)

	engine = Engine()
	callback = functools.partial(cb, sock)
	engine.add_handler(sock.fileno(), callback, Engine.READ)
	engine.start()
