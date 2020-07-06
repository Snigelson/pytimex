import pytimex

def listhex(pkg):
	outstr = ""
	for b in pkg:
		outstr += "0x{:02x}, ".format(b)
	return outstr[:-1]

# Setup data to be sent
d = pytimex.TimexData()

# Try all the features!
a = d.addNewAppointment(5, 31, 0x27, "meet a guy? ")
d.addNewTodo(3, "buy coffee")
d.addNewTodo(12, "code stuff") # Priority C
d.addNewPhoneNumber("5P4C3", "e.t. home")
d.addNewPhoneNumber("0722339677", "some guy")
d.addNewAnniversary(6, 6, "national day")

# You can modify the objects from above later:
a.label = "funny meeting"

# Setup two timezones
d.setTimezone(1, +2, 24, "cet")
d.setTimezone(2, 0, 24, "utc")
d.sendTime = True

# Add some alarms.
# You can overwrite them individually, but currently I have no way of specifying
# alarm ID here.
d.addNewAlarm(7,0,0,0,"wake up@",True)
d.addNewAlarm(hour=10, minute=15, month=0, day=30, label="monthly meeting", audible=True)

# Get data to be transferred
data = bytes(d)

# Show data, for debugging
print("Data to be blasted:")
print(listhex(data))
print("")

# Initialize blaster
b = pytimex.Blaster("/dev/ttyACM0")

if not b.identify():
	print("Could not verify adapter :(")
	sys.exit(-1)

print("Sending data...")

# Send synchronization bytes (0x55 and 0xAA)
b.send_sync()

# Blast data
for databyte in data:
	b.blast(databyte)

print("Done!")

