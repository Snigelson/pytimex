import pytimex

def listhex(pkg):
	outstr = ""
	for b in pkg:
		outstr += "0x{:02x}, ".format(b)
	return outstr[:-1]

# Setup data to be sent
d = pytimex.TimexData()

if 0:
	# Try all the features!
	a = d.addNewAppointment(5, 31, 0x27, "test")
	d.addNewTodo(3, "code stuff")
	d.addNewPhoneNumber(73579, "e.t. home")
	d.addNewAnniversary(6, 6, "national day")

	# You can modify these later:
	a.label = "hello"

	# Setup a good timezone and a silly one just for testing
	d.setTimezone(1, +2, 24, "cet")
	d.setTimezone(2, -4.5, 24, "hej")
	d.sendTime = True

	# Add some alarms.
	# Don't know if you need to send all five at once or if you can overwrite them individually.
	d.addNewAlarm(9,0,0,0,"sample",True)
	d.addNewAlarm(hour=10, minute=15, month=0, day=30, label="plug meeting", audible=True)
	d.addNewAlarm(0, 0, 0, 0, "test", False)
	d.addNewAlarm(0, 0, 0, 0, "alarm #4", False)
	d.addNewAlarm(0, 0, 0, 0, "alarm #5", False)
else:
	d.setTimezone(1, +2, 24, "cet")
	d.setTimezone(2, -4.5, 24, "hej")
	d.sendTime = True

# Get data to be transferred
data = bytes(d)

# Show data, for debugging
print("Data to be blasted:")
print(listhex(data))

sys.exit(0)

# Initialize blaster
b = pytimex.Blaster("/dev/ttyACM0", syncbuflen=16)

if not b.identify():
	print("Could not verify adapter :(")
	sys.exit(-1)

# Send synchronization byes (0x55 and 0xAA)
b.send_sync()

# Blast data
for databyte in data:
	b.blast(databyte)

# Flush and wait for all bytes to sync
b.flush()

print("Done!")

