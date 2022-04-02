#!/usr/bin/python3

import serial
import time
import sys


"""
On reset the device can respond to 3 commands:

* 'x': Device detection, echo this so the PC knows you're there
* '?': Device ID query, reply with "M764" and a null byte ('\0')
* 'U': Reply with 'x' and enter transmit mode

In transmit mode, all bytes should be echoed back to the PC and the
commands above should not be answered. Transmit mode is only left upon
reset.
"""


if len(sys.argv) not in [3,4]:
	print("Usage: {} <port> <log file> [bin|txt]".format(sys.argv[0]))
	sys.exit(-1)

serialPort = sys.argv[1]
logFileName = sys.argv[2]

logText = False

if len(sys.argv) == 4:
	if sys.argv[3] == "txt":
		logText = True

# Used for rudimentary packet parsing
pastSync = 0
packetLeft = -1

with serial.Serial(serialPort, 9600) as sp:

	# Used to control state of device
	transmitState = False

	def send(data):
		sp.write(data)

	while True:
		inb = sp.read(1)
		if len(inb) == 0:
			break

#		print("CTS: {}\tDSR: {}\tRI: {}\tCD: {}".format(sp.cts,sp.dsr,sp.ri,sp.cd))

		if not transmitState:
			if inb == b"x":
				print("Received detection byte ('x')")
				send(inb)

			elif inb == b"?":
				print("Received device ID query ('?')")
				send("?M764\0".encode())

			elif inb == b"U":
				print("Received sync byte, entering transmit state")
				transmitState = True
				logfile = open(logFileName, 'wb')
				send(inb)

			else:
				print("Received unknown byte ({}) outside of transmit state".format(inb))

		else:
			if pastSync == 0 and inb != b'U':
				pastSync = 1
				logfile.write("\n".encode())

			if pastSync == 1 and inb != b'\xAA':
				pastSync = 2
				packetLeft = 0

			if pastSync == 2 and packetLeft == 0:
				packetLeft = ord(inb)
				logfile.write("\n".encode())

			if logText:
				logfile.write(("0x{:02x} ".format(ord(inb))).encode())
				if packetLeft > 0:
					packetLeft -= 1
			else:
				logfile.write(inb)

			send(inb)
