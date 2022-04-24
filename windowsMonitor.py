import os
import time
import ctypes
import win32con
import threading
import ctypes.wintypes

from runable import Runable

class WindowsMonitor(Runable):
	user32 = ctypes.windll.user32
	ole32 = ctypes.windll.ole32
	kernel32 = ctypes.windll.kernel32

	threadFlag = getattr(win32con, 'THREAD_QUERY_LIMITED_INFORMATION', win32con.THREAD_QUERY_INFORMATION)
	processFlag = getattr(win32con, 'PROCESS_QUERY_LIMITED_INFORMATION', win32con.PROCESS_QUERY_INFORMATION)

	def __init__(self, core, focuCallback):
		super().__init__()

		self.core = core
		self.focuCallback = focuCallback

	def _onStart(self):
		threading.Thread(target=self._monitorThread).start()
		
	def _monitorThread(self):
		winEventProcType = ctypes.WINFUNCTYPE(
			None,
			ctypes.wintypes.HANDLE,
			ctypes.wintypes.DWORD,
			ctypes.wintypes.HWND,
			ctypes.wintypes.LONG,
			ctypes.wintypes.LONG,
			ctypes.wintypes.DWORD,
			ctypes.wintypes.DWORD
		)

		self.ole32.CoInitialize(0)

		winEventProc = winEventProcType(self._eventHandler)
		self.user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

		hookId = self.user32.SetWinEventHook(
			win32con.EVENT_OBJECT_FOCUS,
			win32con.EVENT_OBJECT_FOCUS,
			0,
			winEventProc,
			0,
			0,
			win32con.WINEVENT_OUTOFCONTEXT )

		message = ctypes.wintypes.MSG()
		while self.user32.GetMessageW(ctypes.byref(message), 0, 0, 0) != 0:
			self.user32.TranslateMessageW(message)
			self.user32.DispatchMessageW(message)

		self.user32.UnhookWinEvent(hookId)
		self.ole32.CoUninitialize()

	@classmethod
	def _setHook(cls, winEventProc, eventType):
		return cls.user32.SetWinEventHook(eventType, eventType, 0, winEventProc, 0, 0, win32con.WINEVENT_OUTOFCONTEXT)

	@classmethod
	def getProcessId(cls, dwEventThread, hwnd):
		hThread = cls.kernel32.OpenThread(cls.threadFlag, 0, dwEventThread)

		if hThread:
			try:
				processId = cls.kernel32.GetProcessIdOfThread(hThread)
				if not processId:
					print("Couldn't get process for thread %s: %s" %
							 (hThread, ctypes.WinError()))
			finally:
				cls.kernel32.CloseHandle(hThread)
		else:
			errors = ["No thread handle for %s: %s" %
					  (dwEventThread, ctypes.WinError(),)]

			if hwnd:
				processId = ctypes.wintypes.DWORD()
				threadId = user32.GetWindowThreadProcessId(
					hwnd, ctypes.byref(processId))
				if threadId != dwEventThread:
					print("Window thread != event thread? %s != %s" %
							(threadId, dwEventThread))
				if processId:
					processId = processId.value
				else:
					errors.append(
						"GetWindowThreadProcessId(%s) didn't work either: %s" % (
						hwnd, ctypes.WinError()))
					processId = None
			else:
				processId = None

			if not processId:
				for err in errors:
					print(err)

		return processId

	@classmethod
	def getProcessFilename(cls, processId):
		hProcess = cls.kernel32.OpenProcess(cls.processFlag, 0, processId)
		if not hProcess:
			print("OpenProcess(%s) failed: %s" % (processId, ctypes.WinError()))
			return None

		try:
			filenameBufferSize = ctypes.wintypes.DWORD(4096)
			filename = ctypes.create_unicode_buffer(filenameBufferSize.value)
			cls.kernel32.QueryFullProcessImageNameW(hProcess, 0, ctypes.byref(filename), ctypes.byref(filenameBufferSize))

			return filename.value
		finally:
			cls.kernel32.CloseHandle(hProcess)

	def _eventHandler(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
		length = self.user32.GetWindowTextLengthW(hwnd)
		title = ctypes.create_unicode_buffer(length + 1)
		self.user32.GetWindowTextW(hwnd, title, length + 1)

		processId = self.getProcessId(dwEventThread, hwnd)
		processPath = self.getProcessFilename(processId)
		processFilename = os.path.basename(processPath)

		self.focuCallback(processFilename, title.value)

if __name__ == "__main__":
	m = WindowsMonitor(None, print)
	m.start()

	while True:
		try:
			time.sleep(1)
		except:
			os._exit(1)