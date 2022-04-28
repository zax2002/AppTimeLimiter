import os
import re
import time
import threading
import win10toast

from utils import Utils
from runnable import Runnable

class LimitedApp(Runnable):
	def __init__(self, processFilename, regex, timeAllowed):
		super().__init__()

		self.toastNotifier = win10toast.ToastNotifier()

		self.processFilename = processFilename
		self.regex = re.compile(regex)
		self.timeAllowed = Utils.parseTime(timeAllowed)

		self.focused = False
		self.focusTime = None

		self.timeUsed = 0

		self.timers = []

	def _onStop(self):
		self._cancelTimers()


	def match(self, processFilename, title):
		return processFilename == self.processFilename and self.regex.match(title)

	def onFocus(self):
		if self.focused:
			return

		self.focusTime = time.time()

		if self.isExpired():
			self._kill()
			return

		self.focused = True

		timeLeft = self.getTimeLeft()

		self.timers = []

		if timeLeft > 5:
			self.timers.append(threading.Timer(timeLeft - 5, self._notification, args=("5..", 0.6)))
			self.timers.append(threading.Timer(timeLeft - 4, self._notification, args=("4..", 0.6)))
			self.timers.append(threading.Timer(timeLeft - 3, self._notification, args=("3..", 0.6)))
			self.timers.append(threading.Timer(timeLeft - 2, self._notification, args=("2..", 0.6)))
			self.timers.append(threading.Timer(timeLeft - 1, self._notification, args=("1..", 0.6)))

		if timeLeft > 60:
			self.timers.append(threading.Timer(timeLeft - 60, self._notification, args=("1 minute left",)))

		if timeLeft > 5*60:
			self.timers.append(threading.Timer(timeLeft - 5*60, self._notification, args=("5 minutes left",)))

		if timeLeft > 10*60:
			self.timers.append(threading.Timer(timeLeft - 10*60, self._notification, args=("10 minutes left",)))


		self.timers.append(threading.Timer(timeLeft, self._kill))

		for timer in self.timers:
			timer.start()

	def onBlur(self):
		if not self.focused or self.focusTime is None:
			return

		self.focused = False

		self._cancelTimers()

		self.timers = []

		self.timeUsed += time.time() - self.focusTime

	# Time -----------------------------------------------------------------------------------------

	def getTimeUsed(self):
		if not self.focused or self.focusTime is None:
			return self.timeUsed
		
		return self.timeUsed + (time.time() - self.focusTime)

	def isExpired(self):
		return self.getTimeUsed() >= self.timeAllowed

	def resetTime(self):
		self.timeUsed = 0
		self.focusTime = None
		
		self.restartTimers()

	def getTimeLeft(self):
		timeLeft = self.timeAllowed - self.getTimeUsed()
		return timeLeft if timeLeft >= 0 else 0

	def setTimeLeft(self, timeSeconds):
		self.timeUsed = self.timeAllowed - timeSeconds
		self.restartTimers()

	def setTimeAllowed(self, timeSeconds):
		self.timeAllowed = timeSeconds
		self.restartTimers()

	# Timers ---------------------------------------------------------------------------------------

	def restartTimers(self):
		self._cancelTimers()

		if self.focused:
			self.focused = False
			self.onFocus()

	def _cancelTimers(self):
		for timer in self.timers:
			try:
				timer.cancel()
			except:
				pass

	def _notification(self, text, duration=5, title="TimeLimiter"):
		self.toastNotifier.show_toast(title, text, duration=duration, threaded=True)

	def _countdown(self):
		for i in range(5, 0, -1):
			self._notification(f"{i}..", duration=1)
			time.sleep(1)

	def _kill(self):
		self._notification("Sorry")
		os.system(f"taskkill /f /im {self.processFilename}")