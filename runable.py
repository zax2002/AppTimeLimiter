class Runable:
	def __init__(self):
		self.running = False

	def start(self, *_args, **__args):
		if self.running:
			return

		self.running = True

		self._onStart(*_args, **__args)

	def stop(self, *_args, **__args):
		if not self.running:
			return

		self.running = False

		self._onStop(*_args, **__args)

	def _onStart(self):
		pass

	def _onStop(self):
		pass