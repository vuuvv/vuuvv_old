import re
import sys
import time
import urllib
import functools
sys.path.insert(0, "..")
from urllib.parse import urlparse

from vuuvv.core.engine import Engine, Task
from vuuvv.core.connection import Connection

count = 0

class HTTPClient(object):
	def _fetch(self, url):
		global count
		if count % 100 == 0:
			print(count)
		self.start_time = time.time()
		parsed = urlparse(url)
		netloc = parsed.netloc
		if "@" in netloc:
			userpass, _, netloc = netloc.rpartition("@")
		match = re.match(r'^(.+):(\d+)$', netloc)
		if match:
			host = match.group(1)
			port = int(match.group(2))
		else:
			host = netloc
			port = 80
		conn = Connection()
		conn.connect((host, port))
		headers = {
			"Connection": "close",
			"Host": netloc,
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
			"Accept-Encoding": "gzip, deflate",
			"User-Agent": "vuuvv",
		}
		request = (b"GET / HTTP/1.1\r\n")
		request += b'\r\n'.join([("%s: %s" % (k, v)).encode() for k, v in headers.items()])
		request += b'\r\n\r\n'
		conn.write(request)
		data = conn.read_until(b'\r\n\r\n')
		conn.close()
		count += 1

	def fetch(self, url, engine=None):
		Task(functools.partial(self._fetch, url)).start()

def main():
	i = 0
	while i != 600:
		HTTPClient().fetch("http://localhost:8088/")
		i += 1

if __name__ == '__main__':
	Task(main).start()
