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

The device is powered from the CTS control line, so this is pulled down
at the beginning of transmission to make sure the device is reset.
"""


if len(sys.argv) != 3 and len(sys.argv) != 4:
	print("Usage: {} <port> <log file> [bin|txt]".format(sys.argv[0]))
	sys.exit(-1)

serialPort = sys.argv[1]
logFileName = sys.argv[2]

logText = False

if len(sys.argv) == 4:
	if sys.argv[4] == txt:
		logText = True

with serial.Serial(serialPort, 9600, timeout=0.1) as sp:

	# Used to control state of device
	transmitState = False

	def send(data):
#		print("Sending: '{}'".format(data))
		sp.write(data)

	while True:
		while True:
			# CTS control line is used for powering device, and therefore also reset it
			if False and sp.cts == False:
				if transmitState:
					print("Leaving transmit state")
					logfile.close()
				transmitState = False
			inb = sp.read(1)
			if len(inb) != 0:
				break

		print("Received: {}".format(inb))

		if not transmitState:
			if inb == b"x":
				print("Received detection byte ('x')")
				send(inb)

			elif inb == b"?":
				print("Received device ID query ('?')")
				send("M764\0".encode())

			elif inb == b"U":
				print("Received sync byte, entering transmit state")
				transmitState = True
				logfile = open(logFileName, 'wb')
				send(inb)

			else:
				print("Received unknown byte ({}) outside of transmit state".format(inb))

		else:
			if logText:
				logfile.write(("0x{:02x} \n".format(ord(inb))).encode())
			else:
				logfile.write(inb)
			send(inb)
