import traceback
from runable import Runable

class CLI(Runable):
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

		self._addCommand("list",
			self._listCommand,
			"List all limited apps" )

	def dispatchCommand(self, clientInput):
		command, *args = clientInput.split(" ")

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
				self.response(traceback.format_exception(e))

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

	# ----------------------------------------------------------------------------------------------

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
		for limit in self.core.limiter.limits:
			self.response(f"{limit.processFilename} {limit.getTimeLeft()} / {limit.timeAllowed}")