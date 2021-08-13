import datetime
from ._helpers import *

class WatchModel:
	def __init__(self, name="DL50", protocol=1):
		self.name = name
		self.protocol = protocol

	def __str__(self):
		return self.name

DL50   = WatchModel('DL50', 1) # I think this uses the same protocol as the 70
DL70   = WatchModel('DL70', 1)
DL150  = WatchModel('DL150', 3)
DL150s = WatchModel('DL150s', 4)


# Month name lookup
monthNamesAbbr = [
	"<unknown>", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
	"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

class TimexAppointment:
	def __init__(self, month=0, day=0, time=0, label=""):
		self.month=month
		self.day=day
		self.time=time
		self.label=label

	def __str__(self):
		ctime = "{:02}:{:02}".format(int(self.time/4), (self.time&0x03)*15)
		return "Appointment on the {} of {} at {}, label \"{}\"".format(
			self.day, monthNamesAbbr[self.month], ctime, self.label)

	def __bytes__(self):
		data = [self.month&0xFF, self.day&0xFF, self.time&0xFF]
		data = data + pack4to3(str2timex(self.label))
		data = [len(data)+1] + data
		return bytes(data)


class TimexTodo:
	def __init__(self, 	prio=0, label=""):
		self.prio=prio
		self.label=label

	def __str__(self):
		p = "priority {}".format(self.prio) if self.prio else "no priority"
		return "Todo with {}, label \"{}\"".format(
			p, self.label)

	def __bytes__(self):
		data = [self.prio]
		data = data + pack4to3(str2timex(self.label))
		data = [len(data)+1] + data
		return bytes(data)


class TimexPhoneNumber:
	def __init__(self, 	number="1", label=""):
		self.number=number
		self.label=label

	def __str__(self):
		return "Phone number {}, label \"{}\"".format(
			self.number, self.label)

	def __bytes__(self):
		# TODO: This only works with numbers 10 digits or less, and no type indication
		# Convert to digits
		conv_table = {
			'0':  0, '1':  1, '2':  2, '3':  3, '4':  4, '5':  5, '6':  6, '7':  7,
			'8':  8, '9':  9, 'C': 10, 'F': 11, 'H': 12, 'P': 13, 'W': 14, ' ': 15
		}
		digits = [conv_table[x] for x in str(self.number)]
		# Pad with spaces
		t = [15]*12 # Make a "template" filled with char 15
		t[-2-len(digits):-2] = digits # Replace part of template
		# Smush it up
		data = [d[1]<<4|d[0] for d in zip(t[0::2], t[1::2]) ]

		data = data + pack4to3(str2timex(self.label))
		data = [len(data)+1] + data

		return bytes(data)


class TimexAnniversary:
	def __init__(self, 	month=1, day=1, label=""):
		self.month=month
		self.day=day
		self.label=label

	def __str__(self):
		return "Anniversary on the {} of {}, label \"{}\"".format(
			self.day, monthNamesAbbr[self.month], self.label)

	def __bytes__(self):
		data = [self.month&0xFF, self.day&0xFF]
		data = data + pack4to3(str2timex(self.label))
		data = [len(data)+1] + data
		return bytes(data)


class TimexTimezone:
	def __init__(self, offset=0, format=24, name=""):
		self.offset = offset
		self.format = format
		self.name = name

	@property
	def format(self):
		return self._format

	@format.setter
	def format(self, f):
		if not f in [12,24]:
			raise Exception("Time format must be 12 or 24 hours")
		self._format = f

	def __str__(self):
		return "Time zone with offset UTC{:+} named \"{}\", {} hour format".format(offset, name, format)


class TimexAlarm:
	def __init__(self, hour=0, minute=0, month=0, day=0, label="", audible=True):
		self.hour = hour
		self.minute = minute
		self.month = month
		self.day = day
		self.label = label
		self.audible = audible

	def __str__(self):
		audible_str = "audible" if self.audible else "inaudible"

		if self.day==0 and self.month==0:
			return "Alarm at {:02d}:{:02d}, label \"{}\", {}".format(
				self.hour, self.minute, self.label, audible_str)

		if self.day==0:
			return "Alarm at {:02d}:{:02d} every day in {}, label \"{}\", {}".format(
				self.hour, self.minute, monthNamesAbbr[self.month], self.label, audible_str)

		if self.month==0:
			return "Alarm at {:02d}:{:02d} on the {}, label \"{}\", {}".format(
				self.hour, self.minute, self.day, self.label, audible_str)

		return "Alarm at {:02d}:{:02d} on the {} of {}, label \"{}\", {}".format(
			self.hour, self.minute, self.day, monthNamesAbbr[self.month], self.label, audible_str)


class TimexData:
	def __init__(self, model=DL70):
		self.appointments = []
		self.todos = []
		self.phonenumbers = []
		self.anniversaries = []
		self.alarms = []
		self.sendTime = False
		self.tz=[
			TimexTimezone(0, 24, "utc"),
			TimexTimezone(-5, 12, "est")
		]
		# Number of seconds to add to time when blasting, to compensate
		# for the time between building the packet and the watch
		# receiving it.
		self.secondsOffset=8
		self.model=model

	def setTimezone(self, tzno, offset, format, name):
		if tzno not in [1,2]:
			raise Exception("Time zone number must be 1 or 2!")

		if len(name)>3:
			raise Exception("Max length for time zone name is 3 characters!")

		self.tz[tzno-1] = TimexTimezone(offset, format, name)

	def addAppointment(self, appointment):
		self.appointments.append(appointment)

	def addNewAppointment(self, *args, **kwargs):
		new = TimexAppointment(*args, **kwargs)
		self.addAppointment(new)
		return new

	def delAppointment(self, appointment):
		self.appointments = [a for a in self.appointments if a != appointment]

	def addTodo(self, todo):
		self.todos.append(todo)

	def addNewTodo(self, *args, **kwargs):
		new = TimexTodo(*args, **kwargs)
		self.addTodo(new)
		return new

	def delTodo(self, todo):
		self.todos = [a for a in self.todos if a != todo]

	def addPhoneNumber(self, phonenumber):
		self.phonenumbers.append(phonenumber)

	def addNewPhoneNumber(self, *args, **kwargs):
		new = TimexPhoneNumber(*args, **kwargs)
		self.addPhoneNumber(new)
		return new

	def delPhoneNumber(self, phonenumber):
		self.phonenumbers = [a for a in self.phonenumbers if a != phonenumber]

	def addAnniversary(self, anniversary):
		self.anniversaries.append(anniversary)

	def addNewAnniversary(self, *args, **kwargs):
		new = TimexAnniversary(*args, **kwargs)
		self.addAnniversary(new)
		return new

	def delAnniversary(self, anniversary):
		self.anniversaries = [a for a in self.anniversaries if a != anniversary]

	def addAlarm(self, alarm):
		self.alarms.append(alarm)

	def addNewAlarm(self, *args, **kwargs):
		new = TimexAlarm(*args, **kwargs)
		self.addAlarm(new)
		return new

	def delAlarm(self, alarm):
		self.alarms = [a for a in self.alarms if a != alarm]

	def __bytes__(self):
		data = b''

		data += bytes(makeSTART1(version=self.model.protocol))

		if self.sendTime:
			now = datetime.datetime.utcnow() + datetime.timedelta(0,self.secondsOffset)
			tz1time = now+datetime.timedelta(hours=self.tz[0].offset)
			tz2time = now+datetime.timedelta(hours=self.tz[1].offset)
			if self.model.protocol == 1:
				data += bytes(makeTZ(2, tz2time, self.tz[1].format))
				data += bytes(makeTZ(1, tz1time, self.tz[0].format))
				data += bytes(makeTZNAME(1, self.tz[0].name))
				data += bytes(makeTZNAME(2, self.tz[1].name))
			elif self.model.protocol == 3 or self.model.protocol == 4:
				data += bytes(makeTIMETZ(1, tz1time, self.tz[0].format, self.tz[0].name))
				data += bytes(makeTIMETZ(2, tz2time, self.tz[1].format, self.tz[1].name))

		if (
			len(self.appointments)>0 or
			len(self.todos)>0 or
			len(self.phonenumbers)>0 or
			len(self.anniversaries)>0
		):
			data += bytes(makeSTART2(DATA1_num_packets(self.appointments, self.todos, self.phonenumbers, self.anniversaries)))
			data += bytes(makeDATA1(self.appointments, self.todos, self.phonenumbers, self.anniversaries))
			data += bytes(makeEND1())

		# It's not necessary to send all alarms at once. Though this
		# will leave the alarms not explicitly overwritten. So it might
		## be a good idea to do that. Or make it an option?
		if len(self.alarms)>0:
			i=1
			for a in self.alarms:
				data += makeALARM(a, i)
				i+=1

		data += bytes(makeEND2())

		return data
