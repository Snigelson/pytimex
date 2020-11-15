# Currently only implemented for model 70.

from crccheck.crc import CrcArc
from math import ceil

# Create character conversion table (to be verified)
# Called at first call of str2timex
char_conv = None
def make_char_conv():
	global char_conv

	# All lowercase characters. Using semicolon (;) for divide symbol and at (@) for bell symbol
	# Underscore, underscored check mark, left arrow, right arrow, big block, small square/terminator
	# Small square can be used only on unpacked strings, since on packed strings it is interpreted as a string terminator.
	dst = "0123456789abcdefghijklmnopqrstuvwxyz !\"#$%&'()*+,-./:\\;=@?ABCDEF"
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
	# Add terminating character
	indata.append(0x3f)

	# Add padding
	while len(indata)%4:
		indata.append(0x00)

	outdata = []
	while len(indata)>0:
		ch1 = indata.pop(0)
		ch2 = indata.pop(0)
		ch3 = indata.pop(0)
		ch4 = indata.pop(0)

		outdata.append( ((ch2&0x03)<<6) | (ch1&0x3F) )
		outdata.append( ((ch3&0x0F)<<4) | ((ch2>>2)&0x0F) )
		outdata.append( ((ch4&0x3F)<<2) | ((ch3&0x30)>>4) )

	# Remove zero bytes at end
	while outdata[-1] == 0x00:
		outdata = outdata[:-1]

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
def makeSTART1(version=1):
	return makepkg([0x20, 0x00, 0x00, version])

# num_data1: Number of data1 packets following
def makeSTART2(num_data1):
	return makepkg([0x60, num_data1])

def makeEND1():
	return makepkg([0x62])

def makeEND2():
	return makepkg([0x21])

def makeDATA1payload(appts, todos, phones, anniversaries, appt_alarm=0xFF):
	payload  = [0,0] # Start index for appointments, to be filled later
	payload += [0,0] # Start index for todos, to be filled later
	payload += [0,0] # Start index for phone numbers, to be filled later
	payload += [0,0] # Start index for anniversaries, to be filled later
	payload += [len(appts)]
	payload += [len(todos)]
	payload += [len(phones)]
	payload += [len(anniversaries)]
	payload += [0x14] if len(anniversaries) else [0] # The old docs had 0x60 here, with a question mark
	payload += [appt_alarm] # Time, in five minute intervals, to alarm before appointments (0xFF for none)

	# Add appointments
	index = len(payload)
	payload[0] = (index&0xFF00) >> 8
	payload[1] = (index&0x00FF)
	for a in appts:
		payload += list(bytes(a))

	# Add todos
	index = len(payload)
	payload[2] = (index&0xFF00) >> 8
	payload[3] = (index&0x00FF)
	for a in todos:
		payload += list(bytes(a))

	# Add phone numbers
	index = len(payload)
	payload[4] = (index&0xFF00) >> 8
	payload[5] = (index&0x00FF)
	for a in phones:
		payload += list(bytes(a))

	# Add anniversaries
	index = len(payload)
	payload[6] = (index&0xFF00) >> 8
	payload[7] = (index&0x00FF)
	for a in anniversaries:
		payload += list(bytes(a))

	return payload

# Takes lists of TimexAppointment, TimexTodo, TimexPhoneNumber
# and TimexAnniversary objects. Makes DATA1 payload and splits
# it up as required
def makeDATA1(appts, todos, phones, anniversaries, appt_alarm=0xff):
	payload = makeDATA1payload(appts, todos, phones, anniversaries, appt_alarm=appt_alarm)
	data1packets = []
	index = 0
	while (payload):
		index += 1
		data1packets += makepkg([0x61, index]+payload[:27])
		payload = payload[27:]

	return data1packets

# Returns number of packets required for DATA1
def DATA1_num_packets(appts, todos, phones, anniversaries, appt_alarm=0xff):
	data = makeDATA1payload(appts, todos, phones, anniversaries, appt_alarm=appt_alarm)

	return ceil(len(data)/27)

# Takes lists of TimexAppointment, TimexTodo, TimexPhoneNumber
# and TimexAnniversary objects
def makeDATA1completeBreakfast(appts, todos, phones, anniversaries, appt_alarm=0xff):
	payload = makeDATA1payload(appts, todos, phones, anniversaries, appt_alarm=appt_alarm)
	data1packets = []
	index = 0
	while (payload):
		index += 1
		data1packets += makepkg([0x61, index]+payload[:27])
		payload = payload[27:]

	return makeSTART2(index) + data1packets + makeEND1()

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
