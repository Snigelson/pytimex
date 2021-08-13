# Sends current time to Datalink model 70

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
d = pytimex.TimexData(model=pytimex.DL70)

# Setup two timezones
d.setTimezone(1, +2, 24, "cet")
d.setTimezone(2, 0, 24, "utc")
d.sendTime = True

# Offset adjustment
# The model 70 seems to need a bit more sync than
# the 150, so add a bit more offset
d.secondsOffset=4

# Get data to be transferred
data = bytes(d)

print("Sending data...")

# Send synchronization bytes (0x55 and 0xAA)
blaster.send_sync(times55sync=180, timesAAsync=16)

# Blast data
for databyte in data:
	blaster.blast(databyte)

print("Done!")
