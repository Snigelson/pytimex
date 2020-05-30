import pytimex

def listhex(pkg):
	outstr = ""
	for b in pkg:
		outstr += "0x{:02x}, ".format(b)
	return outstr[:-1]

d = pytimex.TimexData()

#(self, hour=0, minute=0, month=0, day=0, label="", audible=True):
d.addNewAlarm(9,0,0,0,"sample",True)
d.addNewAlarm(1, 1, 5, 21, "test", True)
d.addNewAlarm(0, 0, 0, 23, "example", True)
d.addNewAlarm(0, 10, 1, 0, "alarm #4", False)
d.addNewAlarm(10, 0, 0, 0, "alarm #5", False)

for a in d.alarms:
	print(str(a))

data = bytes(d)
print(listhex(data))
