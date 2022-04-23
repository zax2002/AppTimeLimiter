import ctypes
import win32con
import ctypes.wintypes

from runable import Runable

class WindowsMonitor(Runable):
	def __init__(self, core):
		super().__init__()

		self.core = core

		self.user32 = ctypes.windll.user32
		self.ole32 = ctypes.windll.ole32
		self.kernel32 = ctypes.windll.kernel32