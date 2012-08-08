from greenlet import greenlet

class T(greenlet):
	def __init__(self, func, parent=None):
		super(T, self).__init__(func, parent)

def t1():
	print(12)
	g2.switch()
	print(34)

def t2():
	print(56)
	1/0
	print(78)

import socket
import select
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
select.select([sock.fileno()],[],[],1.0)

g1 = T(t1)
g2 = T(t2)

g1.switch()

