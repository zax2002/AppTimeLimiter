import os
import sys
import json5
import win10toast

from cli import CLI
from runnable import Runnable
from limiter import Limiter
from telnetServer import TelnetServer
from windowsMonitor import WindowsMonitor
from timeTravelDetector import TimeTravelDetector

class Core(Runnable):
	def __init__(self):
		super().__init__()

		self.toastNotifier = win10toast.ToastNotifier()

		self.cli = CLI(self, print, input)
		self.telnetServer = TelnetServer(self)

		self.limiter = Limiter(self)
		self.monitor = WindowsMonitor(self, self.limiter.onWindowFocus)

		self.timeTravelDetector = TimeTravelDetector(self._onTimeTravel)

		if not self.limiter.reloadLimits():
			sys.exit(0)

		if not self.reloadConfig():
			sys.exit(0)

	def _onStart(self):
		if self.config["telnet"]["enabled"]:
			self.telnetServer.setAddress(self.config["telnet"]["host"], self.config["telnet"]["port"])
			self.telnetServer.start()

		self.limiter.start()
		self.monitor.start()

		self.timeTravelDetector.start()

		try:
			self.cli.start()
		except KeyboardInterrupt:
			self.stop()
		except Exception as e:
			print(e)

	def _onStop(self):
		self.cli.stop()
		self.timeTravelDetector.stop()

		if self.telnetServer.running:
			try:
				self.telnetServer.stop("app stopping")
			except:
				pass

		self.monitor.stop()
		self.limiter.stop()

		print("bye")

		#sys.exit(0)
		os._exit(0)

	# ----------------------------------------------------------------------------------------------

	def _onTimeTravel(self, difference):
		print(f"Time travel detected ({difference} seconds)")
		self.limiter.onTimeTravel()

	def notification(self, text, duration=5, title="TimeLimiter"):
		self.toastNotifier.show_toast(title, text, duration=duration, threaded=True)

	def reloadConfig(self):
		print("Loading config..")

		try:
			self.config = json5.load(open("config.json"))

			if self.telnetServer.running:
				if self.telnetServer.host != self.config["telnet"]["host"] or self.telnetServer.port != self.config["telnet"]["port"]:
					print("Restarting telnet server..")
					self.telnetServer.stop("address changed")
					self.telnetServer.setAddress(self.config["telnet"]["host"], self.config["telnet"]["port"])
					self.telnetServer.start()

			return True

		except Exception as e:
			print(f"Failed to reload config: {e}")
			return False

	def reload(self):
		self.reloadConfig()
		self.limiter.reloadLimits()