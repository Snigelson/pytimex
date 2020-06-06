# Data Blaster for Timex
# Will not work with original adapter due to timing issues

import serial
import sys
import time
import struct

class Blaster:
	def __init__(self, portname, syncbuflen=16):
		self.port = serial.Serial(portname, 9600, timeout=0.1)
		time.sleep(2)
		self.to_send = []

	def identify(self):
		return True

	def send_sync(self, times55sync=128, timesAAsync=50):
		for sync in range(times55sync):
			self.blast(0x55)

		for sync in range(timesAAsync):
			self.blast(0xAA)

	def blast(self, data):
		self.to_send.append(data)

	def flush(self):
		self.port.write(struct.pack('!H', len(self.to_send)))
		self.port.write(self.to_send)



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
