import time
import socket
import threading

from cli import CLI
from runnable import Runnable

class TelnetServer(Runnable):
	def __init__(self, core):
		super().__init__()

		self.core = core
		
		self.host = self.port = None
		self.clients = {}

	def _onStart(self):
		if self.host is None:
			self._startError("host is not defined")
			return
		elif self.port is None:
			self._startError("port is not defined")
			return

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			self.socket.bind((self.host, self.port))
		except WindowsError as e:
			if e.winerror == 10048:
				message = "Program is already running or telnet port is already in usage"
				self.core.notification(message)
				print(message)

				time.sleep(2)

				self.core.stop()
				return

			else:
				raise e

		self.socket.listen(10)

		threading.Thread(target=self._serverThread).start()

	def _onStop(self, reason=None):
		print("Stopping telnet server..")

		try:
			self.socket.close()

			for address, connection in self.clients.items():
				if not reason is None:
					try:
						connection.send(f"reason: {reason}\n".encode("utf-8"))
					except:
						pass

				try:
					connection.close()
				except:
					pass

			print("Telnet server stopped")

		except Exception as e:
			print(f"Failed to stop telnet server: {e}")

	def setAddress(self, host, port):
		self.host = host
		self.port = port

	# ----------------------------------------------------------------------------------------------

	def _clientConnected(self, connection, address):
		print(f"[+] {address}")
		self.clients[address] = connection
		threading.Thread(target=self._clientThread, args=(connection, address)).start()

	def _clientDisconnected(self, connection, address):
		print(f"[-] {address}")
		try:
			connection.close()
		except:
			pass

		try:
			del self.connection[address]
		except:
			pass

	def _serverThread(self):
		while self.running:
			try:
				connection, address = self.socket.accept()
				self._clientConnected(connection, address)

			except Exception as e:
				if not self.running:
					break

				print(f"Telnet server thread error: {e}")

	def _clientThread(self, connection, address):
		def responseHandler(message, end="\n"):
			connection.send((message+end).encode("utf-8"))

		def inputProvider():
			try:
				data = connection.recv(4096)
				if not data or data == b"\xff\xf4\xff\xfd\x06":
					self._clientDisconnected(connection, address)
					return None

			except:
				self._clientDisconnected(connection.address)
				return None
			
			return data.decode("utf-8").strip()		


		cli = CLI(self.core, responseHandler, inputProvider)	

		try:
			cli.start()

		except Exception as e:
			print(f"Telnet client thread error: {e}")
			try:
				connection.close()
			except:
				pass


	def _startError(self, message):
		print(f"Failed to start telnet server: {message}")