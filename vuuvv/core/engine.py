import select
import errno
import logging

from greenlet import greenlet, getcurrent

# Constants
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

RUNNING = 0
CLOSING = 1
STOPPED = 2

class Engine(object):
	def __init__(self, impl=None):
		self._impl = impl or _poll()
		self._io_tasks = {}
		self._events = {}
		self._tasks = []
		self._timeouts = []
		self._status = STOPPED

		self._task = greenlet(self._start)

	@classmethod
	def instance(cls):
		instance = getattr(cls, "_instance", None)
		if instance is None:
			instance = Engine()
			cls._instance = instance
		return instance

	@classmethod
	def initialized(cls):
		return getattr(cls, "_instance", None) is not None

	def task(self, func):
		return greenlet(func, self._task)

	def add_io_task(self, fd, func, events):
		self._io_tasks[fd] = self.task(func)
		self._impl.register(fd, events | self.ERROR)

	def update_io_task(self, fd, events):
		self._impl.modify(fd, events | self.ERROR)

	def remove_io_task(self, fd):
		self._io_tasks.pop(fd, None)
		self._events.pop(fd, None)
		try:
			self._impl.unregister(fd)
		except (OSError, IOError):
			logging.debug("Error deleting fd from Engine", exec_info=True)

	def _start(self):
		pass

	def start(self):
		if self._status != STOPPED:
			logging.debug("The engine must have only one instance, status: %d" % self._status)
			return

		# enter main loop
		self._task.switch()

		self._status = STOPPED

	def stop(self):
		self._status = CLOSING

	def running(self):
		return self._status == RUNNING

class _Select(object):
	def __init__(self):
		self.read_fds = set()
		self.write_fds = set()
		self.error_fds = set()
		self.fd_sets = (self.read_fds, self.write_fds, self.error_fds)

	def colse(self):
		pass

	def register(self, fd, events):
		if events & READ:
			self.read_fds.add(fd)
		if events & WRITE:
			self.write_fds.add(fd)
		if events & ERROR:
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
			events[fd] = events.get(fd, 0) | READ
		for fd in writeable:
			events[fd] = events.get(fd, 0) | WRITE
		for fd in errors:
			events[fd] = events.get(fd, 0) | ERROR
		return events.items()

_poll = _Select
