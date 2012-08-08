
class TaskError(Exception):
	"""
	When catch a TaskError, the task will stop.
	"""
	pass

class TimeoutError(TaskError):
	pass

class SyncError(TaskError):
	pass

class SocketError(TaskError):
	def __repr__(self):
		args = self.args
		length = len(args)
		if length == 0:
			return ""
		if length == 1:
			return "Socket error: %s" % args
		return "Socket error on %d: [%d] %s" % (args[2], args[0], args[1])

class SocketClosedUnexpected(SocketError):
	pass

class ConnectError(SocketError):
	def __repr__(self):
		args = self.args
		return "Connect error on %d: [%d] %s" % (args[2], args[0], args[1])

class ReadError(SocketError):
	def __repr__(self):
		args = self.args
		return "Read error on %d: [%d] %s" % (args[2], args[0], args[1])

class WriteError(SocketError):
	def __repr__(self):
		args = self.args
		return "Write error on %d: [%d] %s" % (args[2], args[0], args[1])
