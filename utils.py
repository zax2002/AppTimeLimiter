import datetime

class Utils:
	@classmethod
	def parseTime(cls, time):
		try:
			if time[-1] == "s":
				return int(time[:-1])
			elif time[-1] == "m":
				return int(time[:-1])*60
			elif time[-1] == "h":
				return int(time[:-1])*3600
			elif time[-1] == "d":
				return int(time[:-1])*86400

			return int(time)

		except ValueError:
			return None

	@classmethod
	def secondsToNextDay(cls):
		currentDate = datetime.datetime.now()
		nextDayTime = currentDate.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
		return (nextDayTime - currentDate).total_seconds()