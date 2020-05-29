## pytimex - Timex Data Link watch library

Python libraries for generating and transmitting data to the Timex Data 
Link series of watches using optical data tramsission. Currently only the 
protocol for the original Data Link (50 or 70?) is implemented.

There is a guide [written by dfries]
(https://github.com/dfries/datalink_ironman/blob/github_submodules/datalink/70.txt)
on the Data Link packet encoding. This information was verified using the 
original software, and a few errors were corrected. The data was 
collected using the included script timex_notebook_adapter.py, which 
emulates the Timex Notebook Adapter and logs all bytes sent from the 
program. Much easier than getting it from the CRT!


## TODO

* Implement protocol for 150 and 150s
* Check if all 5 alarms must be sent every time
* Split up DATA1 packets if too long
* Test everything more extensively (most tests have been comparing to
  data from the original Timex software)
* Redo the protocol documentation


## "Timex Notebook Adapter"

A not too intelligent device. Powered by the CTS line of the serial port, 
like many devices of its time. Initially respons to commands "x" (reply 
with "x", used for identification), "?" (reply with "M764\0", probably 
some kind of model name) and "U" (enter send mode, actually 0x55 which is 
the first sync bytes sent). After "U" is received, all bytes are sent 
over the IR LED. To get back to the initial state, device power must be 
cycled. This is done by pulling CTS low for a few hundred milliseconds.

Since I do not have access to an actual adapter, I have no way of
verifying the timings of the device. It's a safe bet, though, that they
will be very similar to those from the CRT.

A one is indicated by the absence of a pulse, a zero is a pulse of about 
32 µs. Pulses are sent at an interval of approximately 480 µs, with some 
jitter. Some configuration files mentioned 2048 baud, which would mean 
approximately 488 µs. So this sort of makes sense.

Bytes are sent least significant bit first, one start bit, no stop bit.
This means the byte 0x5a would look like pnpnppnpn (where p indicates
a pulse, and n the absence of a pulse).

There are some requirements on both the spacing between bytes, and the 
spacing between packages. Using the Notebook Adapter and original 
software, this is done by the PC and the adapter just naively sends the 
data along. Byte spacing seems to be on the order of 2 ms and package
spacing on the order of 240 ms.

When a byte is sent to the adapter, it replies with the same byte. I'm 
assuming it's done to keep things in sync.


## The Blaster

Initially, I implemented the above protocol on an Arduino with hopes of 
being able to both turn it into a replacement adapter for the original 
software and use it with my library, but there were some issues with 
timing. I got it to transfer data correctly when the data was already on 
the Arduino but there were issues when interspersing serial communication 
and turning off interrupts to get the bit timing correct. I might upload 
that version if I can get it working correctly.

The implementation currently in this repository is a lot simpler. It 
reads a data length (2 bytes, big endian), allocates a buffer and reads 
that many bytes, and then transfers them. Sync bytes must be sent by the 
PC, and timing is done entirely on the Arduino.


## Additions/corrections to the github document

Start package contains 0x00 0x00 0x01 for the original Data Link (70?), 
but for model 150 it contains 0x00 0x00 0x03, and for 150s it contains 
0x00 0x00 0x04.

```
zero or more packet type TIME 0x30
byte 1     - timezone   (the watch has two timezones, 1 or 2)
byte 2     - hour
byte 3     - minute
byte 4     - month
byte 5     - day of month
byte 6     - year (last 2 digits)
byte 7     - day of week (0=monday, 6=sunday)
byte 8     - Pretty certain this is seconds
byte 9     - 12h format (1) or 24h format (2)

one package type 0x31 for each time zone - TZNAME
Contains names of timezones, unpacked, timex charset
byte 1    - Time zone number (1 or 2)
byte 2-4  - Name of time zone (e.g. 0x0e 0x1c 0x1d for EST)
```

Checksum seems to be CRC-16/ARC.

For appointment packets, time is indicated in quarters of an hour since 
midnight, if that makes more sense. So for instance 08:45 would be 
8*4+3=35 quarters.

For the 150 models, the protocol seems slightly different. For instance, 
there is a 0x32 package for sending time, combining the 0x30 and 0x31 
packets. Also, the 0x70 packet sent after inaudible alarms is omitted. 
There might be more differences I've yet to uncover. Also proocol for 
apps and sounds are yet to be documented.
