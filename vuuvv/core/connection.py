import sys
import logging

from time import time
from ssl import (SSLSocket, SSL_ERROR_WANT_READ, SSL_ERROR_WANT_WRITE,
				 SSL_ERROR_EOF, SSL_ERROR_ZERO_RETURN, SSL_ERROR_SSL)
from socket import socket, error as socket_error, SOL_SOCKET, SO_ERROR
from errno import EINPROGRESS, EWOULDBLOCK, EAGAIN
from collections import deque
from functools import partial

from .engine import Engine, Task, wait, READ, WRITE, ERROR
from .exceptions import (SocketError, ConnectError, ReadError, WriteError, 
						 TimeoutError, SocketClosedUnexpected)
from vuuvv.utils.error import strerror

def _socket_error_msg(descript, fd, err, msg):
	if status & READ:
		return 

class Connection(object):
	def __init__(self, sock=None, engine=None, max_buffer_size=104857600,
			read_chunk_size=4096):
		self.socket = sock or socket()
		self.fileno = self.socket.fileno()
		self.socket.setblocking(False)
		self.engine = engine or Engine.instance()
		self.max_buffer_size = max_buffer_size
		self.read_chunk_size = read_chunk_size
		self._read_buffer = deque()
		self._read_buffer_size = 0

	def _wait(self, status, deadline, timeout_callback):
		try:
			wait(self.fileno, status, deadline)
		except socket_error as e:
			errno = self.socket.getsockopt(SOL_SOCKET, SO_ERROR)
			self.close()
			raise SocketError(errno, strerror(errno), self.fileno)
		except TimeoutError:
			self.close()
			raise timeout_callback()
		except Exception:
			self.close()
			raise

	def _wait_read(self, deadline, timeout_callback):
		timeout_callback = timeout_callback or self._read_timeout
		self._wait(READ | ERROR, deadline, timeout_callback)

	def _wait_write(self, deadline, timeout_callback):
		timeout_callback = timeout_callback or self._write_timeout
		self._wait(WRITE | ERROR, deadline, timeout_callback)

	def _wait_connect(self, deadline, timeout_callback):
		timeout_callback = timeout_callback or self._connect_timeout
		self._wait(WRITE | ERROR, deadline, timeout_callback)

	def _read_timeout(self):
		return TimeoutError("Read data from %s to %s timout on %d" %
				(self._remote_address, self._local_address, self.fileno))

	def _write_timeout(self):
		return TimeoutError("Write data from %s to %s timout on %d" %
				(self._local_address, self._remote_address, self.fileno))

	def _connect_timeout(self):
		return TimeoutError("Connect to %s timeout on %d" %
				(self._remote_address, self.fileno))

	def close(self):
		sock = self.socket
		if sock is not None:
			self.engine.kill(sock.fileno())
			sock.close()
			self.socket = None

	def connect(self, address, timeout=0):
		deadline = time() + timeout if timeout else None
		sock = self.socket
		try:
			self._remote_address = address
			sock.connect(address)
		except socket_error as e:
			if e.args[0] not in (EINPROGRESS, EWOULDBLOCK):
				self.close()
				raise ConnectError(*(e.args + (self.fileno,)))
		self._wait_connect(deadline, None)
		err = sock.getsockopt(SOL_SOCKET, SO_ERROR)
		if err != 0:
			self.close()
			raise ConnectError(err, strerror(err), self.fileno)
		self._local_address = sock.getsockname()

	def _read(self, deadline, timeout_callback):
		# read the data from socket to _read_buffer
		self._wait_read(deadline, timeout_callback)
		try:
			chunk = self.socket.recv(self.read_chunk_size)
		except socket_error as e:
			# not check the EWOULDBLOCK and EAGAIN error, since we already wait
			self.close()
			raise ReadError(*(e.args + (self.fileno,)))
		if not chunk:
			# socket closed by the other end
			self.close()
			return 0
		self._read_buffer.append(chunk)
		length = len(chunk)
		self._read_buffer_size += length
		if self._read_buffer_size >= self.max_buffer_size:
			self.close()
			raise SocketError("Reached maximum read buffer size")
		return length

	def read(self, n, timeout=0):
		if n == 0:
			return b""

		deadline = time() + timeout if timeout else None

		if self._read_buffer_size >= n:
			# read from buffer
			self._read_buffer_size -= n
			return _deque_pop(self._read_buffer, n)
		else:
			#read from socket
			while True:
				size = self._read(deadline, None)
				if size == 0:
					# socket closed
					self._read_buffer_size = 0
					return _deque_pop(self._read_buffer, n)
				else:
					return self.read(n)

	def read_until(self, delimiter, timeout=0):
		deadline = time() + timeout if timeout else None

		deque = self._read_buffer
		if not deque:
			if self._read(deadline, None) == 0:
				raise SocketClosedUnexpected("Connection is closed and can't "
					"find delimiter:%s" % (delimiter,))

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
				data_len = loc + delimiter_len
				data = chunk[:data_len]
				deque[0] = chunk[data_len:]
				return data
			# not found the delimiter
			if len(deque) == 1:
				# read buffer is exhausted
				if self._read(deadline, None) == 0:
					raise SocketClosedUnexpected("Connection is closed and can't "
						"find delimiter:%s" % (delimiter,))
			else:
				# merge more deque entry
				_merge(deque, merge_size)
				start = max(length - delimiter_len, 0)

	def _write(self, data, deadline, timeout_callback):
		self._wait_write(deadline, timeout_callback)
		try:
			n = self.socket.send(data)
			if n == 0:
				raise socket_error("Write error on %d: %s", self.fileno, e)
		except socket_error as e:
			self.close()
			raise WriteError(*(e.args + (self.fileno,)))

	def write(self, data, timeout=0):
		deadline = time() + timeout if timeout else None
		self._check_closed()
		if not data:
			return
		WRITE_BUFFER_CHUNK_SIZE = 128 * 1024
		if len(data) > WRITE_BUFFER_CHUNK_SIZE:
			for i in range(0, len(data), WRITE_BUFFER_CHUNK_SIZE):
				self._write(data[i:i+WRITE_BUFFER_CHUNK_SIZE], deadline, None)
		else:
			self._write(data, deadline, None)

	def _check_closed(self):
		if not self.socket:
			raise SocketClosedUnexpected("Connection is closed, can't do any "
					"operation.")

def wait_accept(sock, func, engine=None):
	engine = engine or Engine.instance()
	fd = sock.fileno()
	while True:
		try:
			wait(fd, READ, engine=engine)
			client_sock, address = sock.accept()
		except socket_error as e:
			errno = sock.getsockopt(SOL_SOCKET, SO_ERROR)
			if errno != 0:
				engine.kill(fd)
				sock.close()
				raise SocketError(errno, strerror(errno), fd)
		except Exception:
			engine.kill(fd)
			sock.close()
			raise

		conn = Connection(client_sock, engine=engine)
		Task(partial(func, conn, address)).start()

class SSLConnection(Connection):
	def __init__(self, sock, *args, **kwargs):
		self._ssl_options = kwargs.pop('ssl_options', {})
		sock = sock or SSLSocket()
		super(SSLConnection, self).__init__(sock, *args, **kwargs)
		self._ssl_accepting = True
		self._handshake_reading = False
		self._handshake_writing = False

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

