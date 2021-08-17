# Sends sync forever

import sys
import pytimex

print("Looking for blaster...")

try:
	port = sys.argv[1]
except:
	port = "/dev/ttyACM0"

# Initialize blaster
blaster = pytimex.Blaster(port)

print("Sending sync, press ctrl+c to stop")

# Send synchronization byte forever
while True:
	blaster.blast(0x55)
