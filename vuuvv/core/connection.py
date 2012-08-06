from _socket import socket, error as socket_error, SOL_SOCKET, SO_ERROR
from errno import EINPROGRESS, EWOULDBLOCK
from collections import deque

from .engine import Engine, wait_read, wait_write, PollException

class Connection(object):
	def __init__(self, sock=None, engine=None, max_buffer_size=104857600,
			read_chunk_size=4096):
		self.socket = sock or socket()
		self.fileno = self.socket.fileno()
		self.socket.setblocking(False)
		self.engine = engine or Engine.instance()
		self.max_buffer_size = max_buffer_size
		self.read_chunk_size = read_chunk_size
		self.error = None
		self._read_buffer = deque()
		self._read_buffer_size = 0

	def _wait_read(self):
		try:
			wait_read(self.fileno)
		except PollException:
			errno = self.socket.getsocketopt(SOL_SOCKET, SO_ERROR)
			self.error = socket.error(errno, os.strerror(errno))
			self.close()
		except Exception:
			raise

	def _wait_write(self):
		try:
			wait_read(self.fileno)
		except PollException:
			errno = self.socket.getsocketopt(SOL_SOCKET, SO_ERROR)
			self.error = socket.error(errno, os.strerror(errno))
			self.close()
		except Exception:
			raise

	def close(self):
		sock = self.socket
		if sock is not None:
			if any(sys.exc_info()):
				self.error = sys.exc_info()[1]
			self.engine.kill(sock.fileno())
			sock.close()
			self.socket = None

	def connect(self, address):
		try:
			self.socket.connect(address)
		except socket_error as e:
			if e.args[0] not in (EINPROGRESS, EWOULDBLOCK):
				logging.warning("Connect error on fd %d: %s",
					self.fileno, e)
				self.close()
				return
		self._wait_write()
		err = self.socket.getsockopt(SOL_SOCKET, SO_ERROR)
		if err != 0:
			self.error = socket_error(err, os.strerror(err))
			logging.warning("Connect error on fd %d: %s",
					self.fileno, errno.errorcode[err])
			self.close()
			return

	def _read(self):
		# read the data from socket to _read_buffer
		try:
			chunk = self.socket.recv(self.read_chunk_size)
			print("chunk: %s" % chunk)
		except socket_error as e:
			if e.args[0] in (EWOULDBLOCK, EAGAIN):
				# no data in socket buffer
				return 0
			logging.error("Read error on %d: %s", self.fileno, e, exc_info=True)
			self.close()
		if not chunk:
			# socket closed by the other end
			self.close()
			return -1
		self._read_buffer.append(chunk)
		length = len(chunk)
		self._read_buffer_size += length
		if self._read_buffer_size >= self.max_buffer_size:
			logging.error("Reached maximum read buffer size")
			self.close()
			raise IOError("Reached maximum read buffer size")
		return length

	def read(self, n):
		if n == 0:
			return b""

		if self._read_buffer_size >= n:
			# read from buffer
			self._read_buffer_size -= n
			return _deque_pop(self._read_buffer, n)
		else:
			#read from socket
			while True:
				self._wait_read()
				size = self._read()
				print("read from socket %s, %d" % (size, n))
				if size < 0:
					# socket closed
					self._read_buffer_size = 0
					return _deque_pop(self._read_buffer, n)
				elif size == 0:
					# need more
					continue
				else:
					return self.read(n)

	def read_until(self, delimiter):
		deque = self._read_buffer
		# end bytes of last chunk
		delimiter_len = len(delimiter)
		start = 0
		merge_size = self.read_chunk_size

		while True:
			chunk = deque[0]
			length = len(chunk)
			loc = chunk.find(delimiter, start)
			if loc != -1:
				# hit it
				data_len = start + delimiter_len
				data = chunk[:data_len]
				return data
			if length == 1:
				# read buffer is exhausted
				self._wait_read()
			else:
				# merge more deque entry
				_merge(deque, merge_size)
				start = min(length - delimiter_len, 0)

def _merge(deque, min_size):
	"""
	merge entries ahead of the deque, the size is the length first entry
	plus min_size
	"""
	if len(deque) <= 1:
		return
	data = _deque_pop(deque, len(deque[0]) + min_size)
	deque.appendleft(data)

def _deque_pop(deque, size):
	if not size or not deque:
		return b""
	if len(deque) == 1 and len(deque[0]) <= size:
		return deque.pop()
	data = []
	remain = size
	while deque and remain > 0:
		chunk = deque[0]
		if len(chunk) > remain:
			deque[0] = chunk[remain:]
			chunk = chunk[:remain]
		else:
			deque.popleft()
		data.append(chunk)
		remain -= len(chunk)

	return b"".join(data)

