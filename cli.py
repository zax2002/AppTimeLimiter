import traceback

from datetime import timedelta

from utils import Utils
from runnable import Runnable

class CLI(Runnable):
	def __init__(self, core, responseHandler, inputProvider):
		super().__init__()

		self.core = core

		self.response = responseHandler
		self.inputProvider = inputProvider

		self.commands = []
		self.commandAliases = {}

		self._addCommand( ("help", "?", "commands", "cmds"),
			self._helpCommand,
			"Display all the commands" )

		self._addCommand("reload",
			self._reloadCommand,
			"Reload the app" )

		self._addCommand("stop",
			self._stopCommand,
			"Stop the app" )

		self._addCommand(("list", "time"),
			self._listCommand,
			"List all limited apps" )

		self._addCommand("set",
			self._setTimeCommand,
			"Set remaining/allowed time manually" )

	def dispatchCommand(self, clientInput):
		command, *args = clientInput.split(" ")

		command = command.lstrip("/")

		self._onCommand(command, args)

	def _onStart(self):
		self.response("- TimeLimiter Terminal -")

		while self.running:
			self.response("> ", end="")

			clientInput = self.inputProvider()
			if clientInput is None:
				return

			self.dispatchCommand(clientInput)

	# ----------------------------------------------------------------------------------------------

	def _onCommand(self, command, args):
		if command in self.commandAliases:
			try:
				self.commandAliases[command][1](args)
			except Exception as e:
				self.response(f"CLI error:")
				self.response("".join(traceback.format_exception(e)))

		elif command == "":
			return

		else:
			self.response("Unknown command. Type /help to list commands")

	def _addCommand(self, name, handler, description=None):
		if type(name) in (list, tuple, set):
			aliases = name
			command = (aliases, handler, description)

		else:
			aliases = (name,)
			command = (aliases, handler, description)

		self.commands.append(command)

		for alias in aliases:
			self.commandAliases[alias] = command

	# Commands -------------------------------------------------------------------------------------

	def _helpCommand(self, args):
		response = "\nCommands:\n"

		if len(args) > 0:
			response = f"Help for {', '.join(args)}:\n"
			commandsList = args
		else:
			response = "Commands:\n"
			commandsList = [command[0][0] for command in self.commands]

		for commandName in commandsList:
			if commandName in self.commandAliases:
				command = self.commandAliases[commandName]
				if len(command[0]) > 1:
					commandName = f"{command[0][0]} ({', '.join(command[0][1:])})"

				response += f"{commandName}\t-\t{command[2]}\n"

			else:
				self.response(f"Unknown command supplied for help: '{commandName}'")
				return

		self.response(response)

	def _reloadCommand(self, args):
		self.response("Reloading the app..\n")
		self.core.reload()
		self.response("Reloaded")

	def _stopCommand(self, args):
		self.response("Stopping the app..")
		self.core.stop()

	def _listCommand(self, args):
		for i, limit in enumerate(self.core.limiter.limits):
			timeLeft = timedelta(seconds=round(limit.getTimeLeft()))
			timeAllowed = timedelta(seconds=round(limit.timeAllowed))

			barsCount = round(timeLeft/timeAllowed * 50)
			progressBar = "[" + "▄"*barsCount + "_"*(50-barsCount) + "]"

			self.response(f"[{i}] {limit.processFilename}\n  {timeLeft} {progressBar} {timeAllowed}\n")

	def _setTimeCommand(self, args):
		if len(args) < 3 or not args[0] in ("left", "allowed"):
			self.response('Usage: set <"left"|"allowed"> <limitId> <time>')
			return

		timeType, limitIndex, timeSeconds = args[:3]

		try:
			limitIndex = int(limitIndex)
			limit = self.core.limiter.limits[limitIndex]

		except (ValueError, IndexError):
			self.response("Invalid limitId")
			return

		timeSeconds = Utils.parseTime(timeSeconds)
		if timeSeconds is None:
			self.response("Invalid time")
			return

		if timeType == "left":
			limit.setTimeLeft(timeSeconds)
			self.response(f"Remaining time has been set to {timedelta(seconds=timeSeconds)}")

		else:
			limit.setTimeAllowed(timeSeconds)
			self.response(f"Time limit has been set to {timedelta(seconds=timeSeconds)}")
