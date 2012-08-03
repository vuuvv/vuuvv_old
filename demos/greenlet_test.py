from greenlet import greenlet

class T(greenlet):
	def __init__(self, func, parent=None):
		super(T, self).__init__(func, parent)

def t1():
	print(12)
	try:
		g2.switch()
	except Exception as e:
		raise
	print(34)

def t2():
	print(56)
	try:
		1/0
	except Exception as e:
		import sys
		g1.throw(*sys.exc_info())
	print(78)

import socket
import select
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
select.select([sock.fileno()],[],[],1.0)

g1 = T(t1)
g2 = T(t2)

g1.switch()

