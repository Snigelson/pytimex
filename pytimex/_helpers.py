# Currently only implemented for model 70.

from crccheck.crc import CrcArc

# Create character conversion table (to be verified)
# Called at first call of str2timex
"""
char set for labels is:   (6 bits per char)
0-9 : digits
10-36: letters
37-63: symbols:
space !"#$%&'()*+,-./;\
divide =
bell (image, not sound)
?
"""

char_conv = None
def make_char_conv():
	global char_conv

	# All lowercase characters. Using colon (:) for divide symbol and at (@) for bell symbol
	dst = "0123456789abcdefghijklmnopqrstuvwxyz !\"#$%&'()*+,-./;\\:=@?"
	src = range(len(dst))
	char_conv = {k:v for k,v in zip(dst,src)}

# Convert string to timex string format using table from above
def str2timex(string):
	if char_conv is None:
		make_char_conv()
	out = []
	for c in string:
		if not c in char_conv:
			raise Exception("Invalid character {} in string!".format(c))
		out.append(char_conv[c])
	return out

# Pack 4 bytes in 3, used for strings
def pack4to3(indata):
	while len(indata)%4:
		# Add padding
		indata.append(0xff)

	outdata = []
	while len(indata)>0:
		ch1 = indata.pop(0)
		ch2 = indata.pop(0)
		ch3 = indata.pop(0)
		ch4 = indata.pop(0)

		outdata.append( ((ch2&0x03)<<6) | (ch1&0x3F) )
		outdata.append( ((ch3&0x0F)<<4) | ((ch2>>2)&0x0F) )
		outdata.append( ((ch4&0x3F)<<2) | ((ch3&0x30)>>4) )

	return outdata

# Takes a list of bytes, encapsulates and returns final data packet
def makepkg(values):
	packet = []

	packet.append(len(values)+3)

	packet += values

	p = CrcArc()
	p.process(packet)
	crc = p.final()

	packet.append(crc>>8 & 0xFF)
	packet.append(crc & 0xFF)

	return packet

# Just dump list of ints in hex, for debugging convenience
def pkgstr(pkg):
	outstr = ""
	for b in pkg:
		outstr += "0x{:02x} ".format(b)
	return outstr[:-1]

### Packet makers

# Make start package.
def makeSTART1():
	return makepkg([0x20, 0x00, 0x00, 0x01])

# num_data1: Number of data1 packets following
def makeSTART2(num_data1):
	return makepkg([0x60, num_data1])

def makeEND1():
	return makepkg([0x62])

def makeEND2():
	return makepkg([0x21])

# Takes lists of TimexAppointment, TimexTodo, TimexPhoneNumber
# and TimexAnniversary objects
def makeDATA1(appts, todos, phones, anniversaries):
	# TODO: For now, this assumes everything fits in one packet.
	#       If there is a lot of data, this may be split up over
	#       more than one packet.
	data = [1] # Sequence ID
	data += [0,0] # Start index for appointments, to be filled later
	data += [0,0] # Start index for todos, to be filled later
	data += [0,0] # Start index for phone numbers, to be filled later
	data += [0,0] # Start index for anniversaries, to be filled later
	data += [len(appts)]
	data += [len(todos)]
	data += [len(phones)]
	data += [len(anniversaries)]
	data += [0x14] # The github repo had 0x60 here, with a question mark
	data += [0x03] # Time, in five minute intervals, to alarm before appointments

	# Add appointments
	index = len(data)-1
	data[1] = (index&0xFF00) >> 8
	data[2] = (index&0x00FF)
	for a in appts:
		data += list(bytes(a))

	# Add todos
	index = len(data)-1
	data[3] = (index&0xFF00) >> 8
	data[4] = (index&0x00FF)
	for a in todos:
		data += list(bytes(a))

	# Add phone numbers
	index = len(data)-1
	data[5] = (index&0xFF00) >> 8
	data[6] = (index&0x00FF)
	for a in phones:
		data += list(bytes(a))

	# Add anniversaries
	index = len(data)-1
	data[7] = (index&0xFF00) >> 8
	data[8] = (index&0x00FF)
	for a in anniversaries:
		data += list(bytes(a))

	return makepkg([0x61]+data)

# Pass an ID 1 or 2, a datetime object containing current time in this
# timezone and 12 or 24 for time format
def makeTZ(tzno, tztime, format):
	data = [tzno,
		tztime.hour, tztime.minute,
		tztime.month, tztime.day, tztime.year%100,
		tztime.weekday(), tztime.second]

	if format == 12:
		data += [1]
	else:
		data += [2]

	return makepkg([0x30]+data)

def makeTZNAME(tzno, tzname):
	if len(tzname)>3:
		raise Exception("Time zone name too long!")
	elif len(tzname)<3:
		tzname += " "*(3-len(tzname))

	data = [tzno]
	data+= str2timex(tzname)
	return makepkg([0x31]+data)

# Takes an alarm number and a sequence ID (1-5)
def makeALARM(alarm, seq):
	data = [seq]
	data += [alarm.hour, alarm.minute, alarm.month, alarm.day]

	label = alarm.label
	if len(label)<8: # Min 8 chars, pad with space
		label +=" "*(8-len(label))
	label = label[:8] # Max 8 chars
	data += str2timex(label) # NOT packed!

	if alarm.audible:
		data += [1]
	else:
		data += [0]

	pkgdata = makepkg([0x50]+data)

	# Add that packet that's present after inaudible alarms
	if not alarm.audible:
		data = [0, 0x61+seq, 0]
		pkgdata += makepkg([0x70]+data)

	return bytes(pkgdata)
