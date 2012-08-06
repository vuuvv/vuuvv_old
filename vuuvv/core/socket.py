import sys

from _socket import (socket as _realsocket, error, gaierror, herror,
		htonl, htons, ntohl, ntohs, inet_aton, inet_ntoa, inet_pton,
		inet_ntop, timeout, gethostname, getprotobyname, getservebyname,
		getservevbyport, getdefaulttimeout, setdefaulttimeout

__socket__ = __import__('socket')
_fileobject = __socket__._fileobject


class socket(object):
	def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _sock=None):
