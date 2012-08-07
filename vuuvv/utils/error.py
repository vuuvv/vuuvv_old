import os
import sys

def win_error(errno):
	return WinError(errno).args[1]

def format_message(errno):
	return FormatMessage(errno)

def error_tab(errno):
	result = errorTab.get(errno)
	if result is not None:
		return result

try:
	from ctypes import WinError
	strerror = win_error
except ImportError:
	try:
		from win32api import FormatMessage
		strerror = format_message
	except ImportError:
		try:
			from socket import errorTab
			strerror = error_tab
		except ImportError:
			strerror = os.strerror
