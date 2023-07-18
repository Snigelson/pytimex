# Data Blaster for Timex
# Will not work with original adapter due to timing; in the original
# implementation timing is set by the PC

import serial
import sys
import time

class Blaster:
	def __init__(self, portname):
		self.port = serial.Serial(portname, 9600, timeout=0.5)
		time.sleep(2)

	def identify(self):
		self.port.write(b'x')
		indata = self.port.read(1)
		if indata != b'x':
			raise Exception("Transceiver not detected! (x error)")

		self.port.write(b'?')
		indata = self.port.read(5)
		if indata != b'M764\0':
			raise Exception("Transceiver not detected! Got id: {}".format(indata.decode()))

		return True

	def send_sync(self, times55sync=128, timesAAsync=50):
		for sync in range(times55sync):
			self.blast(0x55)

		for sync in range(timesAAsync):
			self.blast(0xAA)

	def blast(self, data):
		self.port.write(bytes([data]))
		rdata = ord(self.port.read(1))
		if not rdata==data:
			raise Exception("Validation error! Wrote {} but received {}".format(data, rdata))

if __name__ == "__main__":
	portname = sys.argv[1]

	b = Blaster(portname)

	if not b.identify():
		print("Could not verify adapter :(")
		sys.exit(-1)

	b.send_sync()
