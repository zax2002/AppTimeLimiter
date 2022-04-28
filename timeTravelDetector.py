import time
import threading

from runnable import Runnable

class TimeTravelDetector(Runnable):
	INTERVAL = 1
	SENSITIVITY = 5

	def __init__(self, callback):
		super().__init__()

		self.onTravel = callback

	def _onStart(self):
		self.lastTime = time.time()

		self._setTimer()

	def _onStop(self):
		try:
			self.timer.cancel()
		except:
			pass

	def _setTimer(self):
		self.timer = threading.Timer(self.INTERVAL, self._thread)
		self.timer.start()

	def _thread(self):
		difference = time.time() - self.lastTime
		if abs(difference) > self.SENSITIVITY:
			try:
				self.onTravel(difference)
			except Exception as e:
				print(f"TimeTravelDetector error: {e}")

		self.lastTime = time.time()

		self._setTimer()

if __name__ == "__main__":
	def onTravel(difference):
		print(f"You travelled {abs(difference)} seconds {'ahead' if difference > 0 else 'behind'}")

	d = TimeTravelDetector(onTravel)
	d.start()