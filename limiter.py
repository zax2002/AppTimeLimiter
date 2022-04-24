import time
import json5
import datetime
import threading

from runable import Runable
from limitedApp import LimitedApp

class Limiter(Runable):
	def __init__(self, core):
		super().__init__()

		self.core = core

		self.focusedApp = None
		self.resetTimer = None

	def _onStart(self):
		self._setResetTimer()


	def _onStop(self):
		print("Stopping limiter..")

		self._cancelResetTimer()

		for limit in self.limits:
			limit.stop()

	def _cancelResetTimer(self):
		try:
			self.resetTimer.cancel()
		except:
			pass

	def _setResetTimer(self):
		self._cancelResetTimer()
		secondsToNextDay = self._getSecondsToNextDay()
		self.resetTimer = threading.Timer(secondsToNextDay, self._resetTime)
		self.resetTimer.start()


	def _resetTime(self):
		for limit in self.limits:
			limit.resetTime()

		time.sleep(60)

		self._setResetTimer()

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