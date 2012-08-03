
from .engine import Engine

class Connection(object):

	def __init__(self, socket, engine=None, max_buffer_size=104857600,
			read_chunk_size=4096):
		self.socket = socket
		self.socket.setblocking(False)
		self.engine = engine or Engine.instance()
		self.max_buffer_size = max_buffer_size
		self.read_chunk_size = read_chunk_size
		self.error = None
