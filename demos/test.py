
if __name__ == '__main__':
	import functools
	import socket
	import sys
	import time
	import errno

	from datetime import timedelta

	sys.path.insert(0, "..")

	from vuuvv.core.engine import Engine, READ, WRITE, Timer, wait_write
	from vuuvv.core.task import Task

	#def cb(sock, fd, events):
	#	while True:
	#		connection, address = sock.accept()
	#		print(fd, events, connection, address)
	#		connection.send(b"Hello")
	#		Task.getcurrent().schedule()

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	#sock.setblocking(0)
	#sock.bind(("localhost", 8888))
	#sock.listen(128)

	engine = Engine.instance()

	def cb(fd, event):
		print("hello", time.time())

	def cb1():
		print("hello")

	def connect():
		sock.setblocking(False)
		try:
			sock.connect(("www.163.com", 80))
		except socket.error as e:
			if e.args[0] not in (errno.EINPROGRESS, errno.EWOULDBLOCK):
				sock.close()
				return
		wait_write(sock.fileno())
		print("connected")
		engine.kill(sock.fileno())
		print("killed")

	#engine.add_timeout(timedelta(seconds=1), cb1)
	#callback = functools.partial(cb, sock)
	#engine.add_io(sock.fileno(), cb1, READ)
	engine.add_task(connect)
	#Timer(cb1, 1000.0).start()
	engine.start()
