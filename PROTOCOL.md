This document is based on [the protocol documentation by Tommy Johnson] 
(https://web.archive.org/web/20030803072005/http://csgrad.cs.vt.edu/~tjohnson/timex/). 
I have added and corrected some information. There may be more differences 
between watch versions, but most information for the model 70 should be 
correct.

The watch I have tested most with is a model 70 which shows 786003 on 
boot. I'm guessing that's some kind of model number or software version.

I also got a hold of a model 150 (802003), and is investing its protocol.
Slightly different but has has the same general structure. Sound and app
packets are not yet documented.


## Physical level

Data is sent as a series of pulses. When sent using th CRT, each byte 
appears as 1-9 horizontal lines, with 2 bytes being sent each frame. A 
CRT draws its image sequentially as it receives the video signal, with 
each line fading shortly after being drawn, so to a light sensor it 
appears as a short pulse. LCDs in general receives an entire frame and 
draws all pixels almost at the same time, which is why LCDs do not work 
for data transfer.

Timex solved this problem by offering a "Notebook Adapter" which 
essentialy is a serially attached unit which transcodes data into the 
appropriate pulses for the watch to receive. This gives us a very nice 
advantage: it is super simple to log data from the program.

Bytes are sent least significant bit first, one start bit, no stop bit. A 
one is indicated by the absence of a pulse, a zero is a pulse. This means 
the byte 0x5a would look like pnpnppnpn (where p indicates a pulse, and n 
the absence of a pulse).

Some measurements were done by probing the video signal. Pulses are 
approximately 32 µs long. Pulses are sent at an interval of approximately 
480 µs. Some configuration files mentioned 2048 baud, which would mean 
approximately 488 µs. So this sort of makes sense.

Data transfer using CRT is done at 640x480@60Hz. At this resolution and 
frequency, the horizontal refresh frequency is 31.46875 kHz, so one line 
is drawn approximately every 31.78 µs. Using these timings, we can 
quantize the above measurements and conclude that one bit is one line and 
a bit is sent every 15 lines. The watch seems to be a bit flexible on 
this though.

Data bytes are separated by approximately 2 ms, and packets are separated 
by approximately 240 ms. The interpacket delay is also present after each 
block of synchronization bytes (i.e. after all 0x55 is sent and after all 
0xAA are sent). The 2 ms interbyte delay happens to be the same time it 
takes to send two bytes at 9600 baud, in this case the computer sending 
the data byte and receiving confirmation it was sent.


## Synchronization

When initiating transfer, first 200 bytes of 0x55 is sent. During this
time the watch will beep and give the user some time to align the watch.
The exact number here is not important.

After that 50 bytes of 0xAA is sent. The original protocol documentation 
says 40 bytes, but I got 50 bytes from the software and I have not 
verified if the exact number is important.


## Strings

Strings are encoded in a special charset, which is referencet to as 
timexscii, timex charset or similar.

The character set is:
```
0123456789
abcdefghijklmnopqrstuvwxyz
 !"#$%&'()*+,-./:\[divide]=[bell symbol]?
[Underscore][underscored check mark][left arrow]
[right arrow][big square][small square]
```

The small square can be used only on unpacked strings, since on packed 
strings it is interpreted as a string terminator.

Since only 6 bits are used per character, the 24 bits of 4 characters can 
be packed into 3 bytes.

First byte:
- High 2 bits contin low bits of second character
- Low 6 bits contain first character

Second byte: 
- High 4 bits contain low bits of third character
- Low 4 bits contain high bits of second character

Third byte:
- High 6 bits contain last character
- Low 2 bits contain high bits of third character

Strings are terminated by a character with all ones (0x3F). If there are 
any 0 bytes after packing, these are removed.

If the above explanation, maybe some pseudo code can clear it up:

```
byte0 = (ch2&0x03)<<6) | (ch1&0x3F)
byte1 = (ch3&0x0F)<<4) | ((ch2>>2)&0x0F)
byte2 = (ch4&0x3F)<<2) | ((ch3&0x30)>>4)
```

Packed string max length is 15 characters + terminator. If there is no 
terminator in the 16 characters, the watch will start displaying its own 
memory.


## Data packets

Data is separated into packets. Each packet has a framing consisting of 
packet length, data type and checksum as follows:

| Byte no. | Description                      |
| -------- | -------------------------------- |
| 1        | Packet lengh (including framing) |
| 2        | Packet type                      |
| 3->len-2 | Payload (if any)                 |
| len-1    | High byte of checksum            |
| len      | Low byte of checksum             |

Checksum is CRC-16/ARC.

When describing packet contents below, only the payload bytes are 
considered. Therefore, "byte 1" would mean the third byte of the packet.


### Packet types

Note that names are made up and not official Timex names.

List is ordered by in which order the watch expects the packets. I will 
probably add more info on order later.

| ID   | Name   | Description                         |
| ---- | ------ | ----------------------------------- |
| 0x20 | START1 | Data transfer start                 |
| 0x30 | TIME   | Time information                    |
| 0x31 | TZNAME | Time zone name                      |
| 0x32 | TIMETZ | Time information and time zone name |
| 0x60 | START2 | Marks start of DATA1 packets        |
| 0x61 | DATA1  | Contains lots of data               |
| 0x62 | END1   | Marks end of DATA1 packets          |
| 0x50 | ALARM  | Alarm data                          |
| 0x70 | SALARM | Sent after silent alarms            |
| 0x21 | END2   | End of data transfer                |

Packets 0x90, 0x91, 0x92, 0x93 and 0x71 are used for data in
version 3. These are only somewhat documented here.

| ID   | Name   | Description                         |
| ---- | ------ | ----------------------------------- |
| 0x90 | START3 | Marks start and type of following packets |
| 0x91 | DATA   |                                     |
| 0x92 | END    |                                     |
| 0x93 | CLEAR  |                                     |
| 0x71 | BEEPS  |                                     |



### 0x20 - START1

Versions: All

| Byte | Description |
| ---- | ----------- |
| 1    | Always 0x00 |
| 2    | Always 0x00 |
| 3    | Version     |

Version is 0x01 for model 70, 0x03 for model 150 and 0x04 for model 150s.

Example packet: 0x07 0x20 0x00 0x00 0x01 0xc0 0x7f


### 0x30 - TIME

Versions: 1

| Byte | Description                      |
| ---- | -------------------------------- |
| 1    | Timezone ID (1 or 2)             |
| 2    | Hour                             |
| 3    | Minute                           |
| 4    | Month                            |
| 5    | Day of month                     |
| 6    | Year (mod 100)                   |
| 7    | Day of week (0=monday, 6=sunday) |
| 8    | Seconds                          |
| 9    | 12h format (1) or 24h format (2) |


### 0x31 - TZNAME

Versions: 1

| Byte | Description                      |
| ---- | -------------------------------- |
| 1    | Timezone ID (1 or 2)             |
| 2    | Character 1 of timezone name     |
| 3    | Character 2 of timezone name     |
| 4    | Character 3 of timezone name     |

Insert spaces on unused characters.

Example: 0x02 0x0e 0x1c 0x1d - timezone 2 named EST


### 0x32 - TIMETZ

Versions: 3, 4

Combination of time packet and time zone name packet. Also includes
information on date format, I believe. For models 150 and 150s.

| Byte | Description                      |
| ---- | -------------------------------- |
| 1    | Timezone ID (1 or 2)             |
| 2    | Second                           |
| 3    | Hour                             |
| 4    | Minute                           |
| 5    | Month                            |
| 6    | Day of month                     |
| 7    | Year (mod 100)                   |
| 8    | Character 1 of timezone name     |
| 9    | Character 2 of timezone name     |
| 10   | Character 3 of timezone name     |
| 11   | Day of week (0=monday, 6=sunday) |
| 12   | 12h format (1) or 24h format (2) |
| 13   | Unknown (always 0x02?) Possibly date format. |




### 0x60 - START2

| Byte | Description                       |
| ---- | --------------------------------- |
| 1    | Number of DATA1 packets to follow |


### 0x61 - DATA1

| Byte | Description                        |
| ---- | ---------------------------------- |
| 1    | Sequence ID (starts at 1)          |
| 2->3 | Start index of appointments        |
| 4->5 | Start index of TODOs               |
| 6->7 | Start index of phone numbers       |
| 8->9 | Start index of anniversaries       |
| 10   | Number of appointments             |
| 11   | Number of TODOs                    |
| 12   | Number of phone numbers            |
| 13   | Number of anniversaries            |
| 14   | Unknown, see below                 |
| 15   | Early alarm, in 5 minute intervals |

Sequence ID is incremented for each DATA1 packet sent.

Indices are counted zero inexed from first address byte (2). This means
the first data is always located at index 0x0e.

The unknown byte was documented as 0x60, but I seem to get 0x14 when 
sending appointments and 0x00 otherwise. Requires some investigating.

Byte 15 indicates how long before appointments, in 5 minute intervals, 
the alarm will sound. Set to 0xFF for no alarm

It seems the maximum length of DATA1 packets sent by original software is 
32 (0x20) bytes. Payloads of packets 2 and forward are just concatenated 
to the first, i.e. no header is added. Header and checksum are not counted
against start indices.

The following data in the payload are records of the following
format:

These 4 record types are found in DATA1 packets:


#### Appointment record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2      | Month                              |
| 3      | Day                                |
| 4      | Time (see below)                   |
| 5->len | Packed string                      |

Time is encoded in 15 minute intervals since midnight, such that 08:45 is 
8*4+3=35.

Model 70: If a value of 90 or higher is used, time will not wrap. 90 will 
show as 24:00, 91 as 24:15, and 255 as 63:45. This will probably not work 
with alarms. Month and day are not boundary checked either.


#### Todo record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2      | Priority (0 or 1-5)                |
| 3->len | Packed string                      |

Original software only sends priority 0 to 5. The number actually 
represents a timexscii character, so any priority up to 63 can be used. 
For 0, no priority is shown on the watch. If you want to show "PRI - 0" 
on the watch, you can set the priority to 64.


#### Phone number record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2-7    | Phone number (BCD, 2 digits per byte, little endian) |
| 8->len | Packed string                      |

Unused digits in phone numbers are set to 0xF.

In the original software, you can set a "type" of number. This can only 
be done for numbers 11 digits or shorter, and the last digit is replaced 
by a character from the table below.

| Type | Description            |
| ---- | ---------------------- |
| 0xA  | Cellular (C)           |
| 0xB  | Fax (F)                |
| 0xC  | Home (H)               |
| 0xD  | Pager (P)              |
| 0xE  | Work (W)               |
| 0xF  | None (No letter shown) |

It seems possible to use these character at any position in the phone
number, if you want.

If phone number is 10 digits or shorter, the last two digits are unused. 
This is done to reserve space for the type, and a space between number 
and type. If the number is 11 digits long, the space between number and 
type is used. If the number is 12 digits long, the type is not included 
and that space is used for a number instead.

Another peculiarity is that you can send multiple numbers for the same 
name by completely omitting the name, not even sendig a string 
terminator, on successive messages. These packets will always be 7 bytes 
long.


#### Anniversary record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2      | Month                              |
| 3      | Day                                |
| 4->len | Packed string                      |


### 0x62 - END1

No payload. Marks end of DATA1 packets.


### 0x50 - ALARM

Versions: 1, 3

| Byte  | Description                        |
| ----- | ---------------------------------- |
| 1     | Alarm ID (starts at 1)             |
| 2     | Hour                               |
| 3     | Minute                             |
| 4     | Month (0 for every month)          |
| 5     | Day (0 for every day)              |
| 6->13 | Label, unpacked                    |
| 14    | 1 if audible, otherwise 0          |

The original software always sends all of the alarms. I suppose that's 
good to keep the alarms guaranteed in synchronization.

Model 70: It seems to be possible to send only some alarms, if you want. 
The alarms that are not sent are unchanged. Sending alarms with index
greater than 5 might make the watch hang. Don't do this.

After silent alarms, send a 0x70, writing 0 to address Alarm ID + 0x61. 
For example, for alarm 3 send 0x70 with payload 0x00 0x64 0x00. I think 
this is sent to patch some firmware error in the watches. To be 
investigated!

Model 150:


### 0x70 - MEM

Versions: 1, 

Didn't know what to call this. Sent after silent alarms on version 1,
not sent on version 3.

| Byte | Description                        |
| ---- | ---------------------------------- |
| 1    | High address                       |
| 2    | Low address                        |
| 3+   | Data to write                      |

According to documentation at http://www.toebes.com/Datalink/download.html,
this is a package to write data to a specific address in memory. Any number
of bytes may be written.


### 0x71 - BEEPS

Versions: 1?, 3

| Byte | Description                        |
| ---- | ---------------------------------- |
| 1    | Hourly chimes (0 off, else on)     |
| 2    | Button beeps (0 off, else on)      |

TODO: Test this


### 0x21 - END2

No payload

