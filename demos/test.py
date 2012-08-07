
if __name__ == '__main__':
	import functools
	import socket
	import sys
	import time
	import errno

	from datetime import timedelta

	sys.path.insert(0, "..")

	from vuuvv.core.engine import Task, Engine, READ, WRITE, Timer, task
	from vuuvv.core.connection import Connection

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

	@task
	def connect():
		conn = Connection()
		conn.connect(("www.163.com", 80), 1)
		print("connected")
		conn.write(b"GET / HTTP/1.1\r\nHost: www.163.com \r\n\r\n")
		data = conn.read_until(b"\r\n\r\n", 2)
		print(data)
		#try:
		#	sock.connect(("smtp.163.com", 25))
		#except socket.error as e:
		#	if e.args[0] not in (errno.EINPROGRESS, errno.EWOULDBLOCK):
		#		sock.close()
		#		return
		#wait_write(sock.fileno())
		#print("connected")
		#wait_read(sock.fileno())
		#print(sock.recv(10))
		#wait_read(sock.fileno())
		#print(sock.recv(10))

	#t = Task(connect)
	#t.start()
	connect()

	#engine.add_timeout(timedelta(seconds=1), cb1)
	#callback = functools.partial(cb, sock)
	#engine.add_io(sock.fileno(), cb1, READ)
	#engine.add_task(connect)
	#Timer(cb1, 1000.0).start()
