import re
import os
import sys
import json5

from cli import CLI
from runable import Runable
from telnetServer import TelnetServer
from windowsMonitor import WindowsMonitor

class TimeLimiter(Runable):
	def __init__(self):
		super().__init__()

		self.cli = CLI(self, print, input)
		self.telnetServer = TelnetServer(self)
		self.monitor = WindowsMonitor(self)

		if not self.reloadLimits():
			sys.exit(0)

		if not self.reloadConfig():
			sys.exit(0)

	def _onStart(self):
		if self.config["telnet"]["enabled"]:
			self.telnetServer.setAddress(self.config["telnet"]["host"], self.config["telnet"]["port"])
			self.telnetServer.start()

		try:
			self.cli.start()
		except KeyboardInterrupt:
			self.stop()
		except Exception as e:
			print(e)

	def _onStop(self):
		self.cli.stop()

		if self.telnetServer.running:
			try:
				self.telnetServer.stop("app stopping")
			except:
				pass

		print("bye")

		sys.exit(0)
		os._exit(0)

	# ----------------------------------------------------------------------------------------------

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

	def reloadLimits(self):
		try:
			limits = json5.load(open("limits.json"))

			self.limits = [[limit["processName"], re.compile(limit["titleMask"])] for limit in limits]

			return True

		except Exception as e:
			print(f"Failed to reload limits: {e}")
			return False

	def reload(self):
		self.reloadConfig()
		self.reloadLimits()