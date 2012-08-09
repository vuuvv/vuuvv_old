from vuuvv.utils.error import strerror

class TaskError(Exception):
	"""
	When catch a TaskError, the task will stop.
	"""
	pass

class TimeoutError(TaskError):
	pass

class SyncError(TaskError):
	pass

class ConnectionError(TaskError):
	def __init__(self, conn, msg=None, errno=None):
		self.remote_addr = conn.remote_address
		self.local_addr = conn.local_address
		self.fd = conn.fileno
		self.msg = msg or "Connection Error"
		self.errno = errno

	def __str__(self):
		msg = self.msg
		parts = []
		if self.errno is not None:
			msg = "%s: %s" % (msg, strerror(self.errno))
			parts.append("errorcode: %d" % self.errno)
		else:
			msg += ": "
		if self.fd is not None:
			parts.append("fd: %d" % self.fd)
		if self.remote_addr is not None:
			parts.append("remote: %s:%d" % self.remote_addr)
		if self.local_addr is not None:
			parts.append("local: %s:%d" % self.local_addr)

		return "%s[%s]." % (msg, ", ".join(parts))

class AcceptError(TaskError):
	pass

