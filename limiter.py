import time
import json5
import datetime
import threading

from runnable import Runnable
from limitedApp import LimitedApp

class Limiter(Runnable):
	def __init__(self, core):
		super().__init__()

		self.core = core

		self.focusedApp = None
		self.resetTimer = None
		self.timerStartDate = None

	def _onStart(self):
		self._setTimer()

	def _onStop(self):
		print("Stopping limiter..")

		self._cancelTimer()

		for limit in self.limits:
			limit.stop()

	# ----------------------------------------------------------------------------------------------

	def _setTimer(self):
		self._cancelTimer()
		secondsToNextDay = self._getSecondsToNextDay()
		self.resetTimer = threading.Timer(secondsToNextDay, self._resetTime)
		self.resetTimer.start()
		self.timerStartDate = datetime.datetime.now()

	def _cancelTimer(self):
		try:
			self.resetTimer.cancel()
		except:
			pass

	def _resetTime(self):
		self._cancelTimer()

		for limit in self.limits:
			limit.resetTime()

		print("Limits has been reset due to the next day")

		time.sleep(1)

		self._setTimer()

	def onTimeTravel(self):
		for limit in self.limits:
			limit.restartTimers()

		if self.timerStartDate is not None and datetime.datetime.now().day != self.timerStartDate.day:
			self._resetTime()

		else:
			self._cancelTimer()
			self._setTimer()

	def reloadLimits(self):
		try:
			limits = json5.load(open("limits.json"))

			self.limits = [LimitedApp(limit["processFilename"], limit["titleRegex"], limit["time"]) for limit in limits]

			return True

		except Exception as e:
			print(f"Failed to reload limits: {e}")
			return False

	def onWindowFocus(self, processFilename, title):
		for limit in self.limits:
			if limit.match(processFilename, title):
				self._onLimitedFocus(limit)
				return

		self._blurPrevious()

	def _onLimitedFocus(self, limit):
		self._blurPrevious()

		limit.onFocus()
		self.focusedApp = limit

	def _blurPrevious(self):
		if not self.focusedApp is None:
			self.focusedApp.onBlur()
			self.focusedApp = None

	@classmethod
	def _getSecondsToNextDay(cls):
		currentDate = datetime.datetime.now()
		nextDayTime = currentDate.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
		# nextDayTime = currentDate + datetime.timedelta(seconds=30)
		return (nextDayTime - currentDate).total_seconds()