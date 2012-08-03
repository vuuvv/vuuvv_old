import select
import errno
import heapq
import logging

from time import time
from datetime import timedelta
from functools import wraps

from .task import Task

#TODO: 对超时的IO进行定期处理

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

		self._task = Task(self._start)

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

	@classmethod
	def wait(cls):
		engine = cls.instance()
		engine._task.switch()

	def task(self, func):
		return Task(func, self._task)

	def add_io(self, fd, func, events):
		self._io_tasks[fd] = self.task(func)
		self._impl.register(fd, events | ERROR)

	def add_io_task(self, fd, task, events):
		self._io_tasks[fd] = task
		self._impl.register(fd, events | ERROR)

	# eg. use when a sock recved a data and now want to send a response
	def update_io_status(self, fd, events):
		self._impl.modify(fd, events | ERROR)

	def remove_io(self, fd):
		self._io_tasks.pop(fd, None)
		self._events.pop(fd, None)
		try:
			self._impl.unregister(fd)
		except (OSError, IOError):
			logging.debug("Error deleting fd from Engine", exec_info=True)

	def add_timeout(self, deadline, callback):
		timeout = _Timeout(deadline, callback, self)
		heapq.heappush(self._timeouts, timeout)
		return timeout

	def remove_timeout(self, timeout):
		timeout.task = None

	def add_task(self, func):
		self._tasks.append(self.task(func))

	def _start(self):
		if self._status != STOPPED:
			logging.warning("The engine must have only one instance, status: %d" % self._status)
			return

		self._status = RUNNING
		while True:
			poll_timeout = 3600.0

			tasks = self._tasks
			self._tasks = []

			for task in tasks:
				task.process()

			#TODO: timeout task
			_timeouts = self._timeouts
			if _timeouts:
				now = time()
				while _timeouts:
					_timeout = _timeouts[0]
					if _timeout.task is None:
						heapq.heappop(_timeouts)
					elif _timeout.deadline <= now:
						heapq.heappop(_timeouts).task.process()
					else:
						seconds = _timeout.deadline - now
						poll_timeout = min(seconds, poll_timeout)
						break

			if self._tasks:
				# if any tasks should run in last round
				poll_timeout = 0.0

			if self._status != RUNNING:
				break

			try:
				event_pairs = self._impl.poll(poll_timeout)
			except Exception as e:
				if (getattr(e, 'errno', None) == errno.EINTR or
					(isinstance(getattr(e, 'args', None), tuple) and
						len(e.args) == 2 and e.args[0] == errno.EINTR)):
					continue
				else:
					raise

			self._events.update(event_pairs)
			while self._events:
				fd, events = self._events.popitem()
				task = self._io_tasks[fd]
				try:
					task.process(fd, events)
				except (OSError, IOError) as e:
					if e.args[0] == errno.EPIPE:
						pass
					else:
						logging.error("Exception in I/O task for fd %s",
							fd, exc_info=True)
				except Exception as e:
					logging.error("Exception in I/O task for fd %s",
						fd, exc_info=True)

		self._status = STOPPED

	def start(self):
		# enter main loop
		try:
			self._task.process()
		except:
			logging.error("Fatal Error", exc_info=True)

	def stop(self):
		self._status = CLOSING

	def running(self):
		return self._status == RUNNING

class _Timeout(object):
	__slots__ = 'deadline', 'callback', 'task'

	def __init__(self, deadline, callback, engine=None):
		if isinstance(deadline, (int, float)):
			self.deadline = deadline
		elif isinstance(deadline, timedelta):
			self.deadline = time() + deadline.total_seconds()
		else:
			raise TypeError("Unsupported deadline %r" % deadline)
		engine = engine or Engine.instance()
		self.task = engine.task(callback)

	def __lt__(self, other):
		return ((self.deadline, id(self)) < (other.deadline, id(other)))

	def __le__(self, other):
		return ((self.deadline, id(self)) <= (other.deadline, id(other)))

class Timer(object):
	def __init__(self, callback, interval, engine=None):
		self.callback = callback
		self.interval = interval
		self.engine = engine or Engine.instance()
		self._running = False
		self._timeout = None

	def start(self):
		self._running = True
		self._schedule_next(time() + self.interval / 1000.0)

	def stop(self):
		self._running = False
		if self._timeout is not None:
			self.engine.remove_timeout(self._timeout)
			self._timeout = None

	def _run(self):
		if not self._running:
			return
		self.callback()

		self._schedule_next(self._last_trigger_time + self.interval / 1000.0)

	def _schedule_next(self, next_deadline):
		if self._running:
			now = time()
			while next_deadline <= now:
				next_deadline += self.interval / 1000.0
			self._last_trigger_time = next_deadline

			self._timeout = self.engine.add_timeout(next_deadline, self._run)

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
