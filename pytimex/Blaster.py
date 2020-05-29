# Data Blaster for Timex
# Will not work with original adapter due to timing issues

import serial
import sys
import time

class Blaster:
	def __init__(self, portname, syncbuflen=16):
		self.port = serial.Serial(portname, 9600, timeout=0.1)
		time.sleep(2)
		self.sent = []
		self.syncbuflen = syncbuflen

	def identify(self):
		self.port.write(b'x')
		indata = self.port.read(1)
		if indata != b'x':
			raise Exception("Transceiver not detected! (x error)")
			return False

		self.port.write(b'?')
		time.sleep(0.2)
		indata = self.port.read(5)
		if indata != b'M764\0':
			print (indata)
			raise Exception("Transceiver not detected! (? error)")
			return False

		return True

	def _checksync(self):
#		print("Sent: "+str(self.sent))

		inbytes = self.port.read(int(self.syncbuflen/2))
		if len(inbytes) == 0:
			return
#		print("Syncing {} byte(s)".format(len(inbytes)))
		for byt in inbytes:
			if byt != self.sent[0]:
				print("Expected {}, got {}".format(self.sent[0], byt))
				raise Exception("Out of sync!")
			self.sent.pop(0)

	def send_sync(self, times55sync=128, timesAAsync=50):
		for sync in range(times55sync):
			self.blast(0x55)

		for sync in range(timesAAsync):
			self.blast(0xAA)

	def blast(self, data):
		self.port.write(bytes([data]))
		self.sent.append(data)

		if len(self.sent)>self.syncbuflen:
			self._checksync()

	def flush(self):
		while len(self.sent)>0:
			self._checksync()

if __name__ == "__main__":
	portname = sys.argv[1]

	b = Blaster(portname, syncbuflen=16)

	if not b.identify():
		print("Could not verify adapter :(")
		sys.exit(-1)

	b.send_sync()

	for p in range(10):
		b.blast(0x03)
		b.blast(0x02)
		b.blast(0x01)

	b.flush()
