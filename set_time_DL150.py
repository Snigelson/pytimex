# Sends current time to Datalink model 150

import sys
import pytimex

print("Looking for blaster...")

try:
	port = sys.argv[1]
except:
	port = "/dev/ttyACM0"

# Initialize blaster
blaster = pytimex.Blaster(port)

# Setup data to be sent
d = pytimex.TimexData(model=pytimex.WatchModels.DL150)

# Setup two timezones
d.setTimezone(1, +2, 24, "cet")
d.setTimezone(2, 0, 24, "utc")
d.sendTime = True

# Offset adjustment
d.secondsOffset=3

# Get data to be transferred
data = bytes(d)

print("Sending data...")

# Send synchronization bytes (0x55 and 0xAA)
blaster.send_sync(times55sync=40, timesAAsync=16)

# Blast data
for databyte in data:
	blaster.blast(databyte)

print("Done!")
