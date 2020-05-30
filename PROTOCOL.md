This document is based on [the protocol documentation by Tommy Johnson] 
(https://web.archive.org/web/20030803072005/http://csgrad.cs.vt.edu/~tjohnson/timex/). 
I have added and corrected some information. There may be more differences 
between watch versions, but most information for the model 70 should be 
correct.

Sound and app packets are not yet documented.


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
is drawn approximately every 31.78 µs. using the above timings, we can 
quantify the above measurement and conclude that one bit is one line and 
a bit is sent every 15 lines. The watch seems to be a bit flexible on
this though.

Data bytes are separated by approximately 2 ms, and packets are separated 
by approximately 240 ms. The interpacket delay is also present after
each block of synchronization bytes.


## Synchronization

When initiating transfer, first 200 bytes of 0x55 is sent. During this
time the watch will beep and give the user some time to align the watch.
The exact number here is not important.

After that 50 bytes of 0xAA is sent. The original protocol documentation 
says 40 bytes, but I got 50 bytes from the software and I have not 
verified if the exact number is important.


## Strings

Strings are encoded in a special charset, which I call the Timex charset.

From the old protocol documentation:

```char set for labels is:   (6 bits per char)
0-9 : digits
10-36: letters
37-63: symbols:
space !"#$%&'()*+,-./;\
divide =
bell (image, not sound)
?```

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

Unused bits are set to ones.

If the above explanation, maybe some pseudo code can clear it up:

```
byte0 = (ch2&0x03)<<6) | (ch1&0x3F)
byte1 = (ch3&0x0F)<<4) | ((ch2>>2)&0x0F)
byte2 = (ch4&0x3F)<<2) | ((ch3&0x30)>>4)
```


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


### 0x20 - START1

| Byte | Description |
| ---- | ----------- |
| 1    | Always 0x00 |
| 2    | Always 0x00 |
| 3    | Version     |

Version is 0x01 for model 70, 0x03 for model 150 and 0x04 for model 150s.

Example packet: 0x07 0x20 0x00 0x00 0x01 0xc0 0x7f


### 0x30 - TIME

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

| Byte | Description                      |
| ---- | -------------------------------- |
| 1    | Timezone ID (1 or 2)             |
| 2    | Character 1 of timezone name     |
| 3    | Character 2 of timezone name     |
| 4    | Character 3 of timezone name     |

Insert spaces on unused characters.

Example: 0x02 0x0e 0x1c 0x1d - timezone 2 named EST


### 0x32 - ALARM2

Alarm packet for model 150 and 150s. To be documented.


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

The unknown byte was documented as 0x60, but I seem to
get 0x14 instead. Requires some investigating.

Byte 15 indicates how long before the specified time the alarm will sound 
(I believe).

Check if the following DATA1 packets contain data start indexes etc too, 
or if their payloads are just concatenated.

The following data in the payload are records of the following
format:

These 4 record types are found in DATA1 packets:

Appointment record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2      | Month                              |
| 3      | Day                                |
| 4      | Time (see below)                   |
| 5->len | Packed string                      |

Time is encoded in 15 minute intervals since midnight, such that 08:45 is 
8*4+3=35.

Todo record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2      | Priority                           |
| 3->len | Packed string                      |

Phone number record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2-6    | Phone number (BCD, 2 digits per byte, little endian) |
| 7->len | Packed string                      |

Anniversary record

| Byte   | Description                        |
| ------ | ---------------------------------- |
| 1      | Record length                      |
| 2      | Month                              |
| 3      | Day                                |
| 4->len | Packed string                      |


### 0x62 - END1

No payload


### 0x50 - ALARM

| Byte  | Description                        |
| ----- | ---------------------------------- |
| 1     | Alarm ID (starts at 1)             |
| 2     | Hour                               |
| 3     | Minute                             |
| 4     | Month (0 for every month)          |
| 5     | Day (0 for every day)              |
| 6->13 | Label, unpacked                    |
| 14    | 1 if audible, otherwise 0          |


### 0x70 - SALARM

Didn't know what to call this. Sent after silent alarms

| Byte | Description                        |
| ---- | ---------------------------------- |
| 1    | Always 0                           |
| 2    | ID of preceding alarm + 0x61       |
| 3    | Always 0                           |


### 0x21 - END2

No payload

