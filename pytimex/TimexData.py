import datetime
from ._helpers import *

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
	def __init__(self, 	prio=1, label=""):
		self.prio=prio
		self.label=label

	def __str__(self):
		return "Todo with priority {}, label \"{}\"".format(
			self.prio, self.label)

	def __bytes__(self):
		data = [self.prio]
		data = data + pack4to3(str2timex(self.label))
		data = [len(data)+1] + data
		return bytes(data)

class TimexPhoneNumber:
	def __init__(self, 	number=1, label=""):
		self.number=number
		self.label=label

	def __str__(self):
		return "Phone number {}, label \"{}\"".format(
			self.number, self.label)

	def __bytes__(self):
		# Encoded as four bits per digit and LSD first, always 10 digits
		digits = [ord(x)-ord('0') for x in "{:010d}".format(self.number)[::-1]]
		data = [d[0]<<4|d[1] for d in zip(digits[0::2], digits[1::2]) ]
		data = data + pack4to3(str2timex(self.label))
		data = [len(data)+1] + data
		return bytes(data)

class TimexAnniversary:
	def __init__(self, 	month=0, day=0, label=""):
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
		self._format = format
		self.name = name

	@property
	def format(self):
		return self._format

	@format.setter
	def format(self, f):
		if not f in [12,24]:
			raise Exception("Time format must be 12 or 24 hours")
		self.format = f

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
	def __init__(self):
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

	def setTimezone(self, tzno, offset, format, name):
		if tzno not in [1,2]:
			raise Exception("Time zone number must be 1 or 2!")

		# TODO: Move these checks to time zone class
		if format not in [12,24]:
			raise Exception("Time format must be 12 or 24!")

		if len(name)>3:
			raise Exception("Max length for time zone name is 3 characters!")

		self.tz[tzno-1] = TimexTimezone(offset, format, name)

	def addAppointment(self, appointment):
		self.appointments.append(appointment)

	def addNewAppointment(self, month=0, day=0, time=0, label=""):
		new = TimexAppointment(month, day, time, label)
		self.addAppointment(new)
		return new

	def delAppointment(self, appointment):
		self.appointments = [a for a in self.appointments if a != appointment]

	def addTodo(self, todo):
		self.todos.append(todo)

	def addNewTodo(self, prio=1, label=""):
		new = TimexTodo(prio, label)
		self.addTodo(new)
		return new

	def delTodo(self, todo):
		self.todos = [a for a in self.todos if a != todo]

	def addPhoneNumber(self, phonenumber):
		self.phonenumbers.append(phonenumber)

	def addNewPhoneNumber(self, number=1, label=""):
		new = TimexPhoneNumber(number, label)
		self.addPhoneNumber(new)
		return new

	def delPhoneNumber(self, phonenumber):
		self.phonenumbers = [a for a in self.phonenumbers if a != phonenumber]

	def addAnniversary(self, anniversary):
		self.anniversaries.append(anniversary)

	def addNewAnniversary(self, month=0, day=0, label=""):
		new = TimexAnniversary(month, day, label)
		self.addAnniversary(new)
		return new

	def delAnniversary(self, anniversary):
		self.anniversaries = [a for a in self.anniversaries if a != anniversary]

	def addAlarm(self, alarm):
		self.alarms.append(alarm)

	def addNewAlarm(self, hour=0, minute=0, month=0, day=0, label="", audible=True):
		new = TimexAlarm(hour, minute, month, day, label, audible)
		self.addAlarm(new)
		return new

	def delAlarm(self, alarm):
		self.alarms = [a for a in self.alarms if a != alarm]

	def __bytes__(self):
		data = b''
		data += bytes(makeSTART1())

		if self.sendTime:
			now = datetime.datetime.utcnow()
			tz1time = now+datetime.timedelta(hours=self.tz[0].offset)
			tz2time = now+datetime.timedelta(hours=self.tz[1].offset)
			data += bytes(makeTZ(2, tz2time, self.tz[1].format))
			data += bytes(makeTZ(1, tz1time, self.tz[0].format))
			data += bytes(makeTZNAME(1, self.tz[0].name))
			data += bytes(makeTZNAME(2, self.tz[1].name))

		if (
			len(self.appointments)>0 or
			len(self.todos)>0 or
			len(self.phonenumbers)>0 or
			len(self.anniversaries)>0
		):
			data += bytes(makeSTART2(1))
			data += bytes(makeDATA1(self.appointments, self.todos, self.phonenumbers, self.anniversaries))
			data += bytes(makeEND1())

		# I don't know if all five alarms must be sent every time.
		# If so, make dummy alarms.
		if len(self.alarms)>0:
			i=1
			for a in self.alarms:
				data += makeALARM(a, i)
				i+=1

		data += bytes(makeEND2())

		return data
