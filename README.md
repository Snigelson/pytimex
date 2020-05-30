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

When a byte is sent to the adapter, it replies with the same byte. I'm 
assuming it's done to keep things in sync.

Since I do not have access to an actual adapter, I have no way of
verifying the timings of the device. It's a safe bet, though, that they
will be very similar to those from the CRT. It is also possible the
data could be sent somewhat faster since it does not need to be phase
locked to the CRT refresh.


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

Hardware wise, you need an Arduino with ATmega328 (168 would probably 
work too) with 16 MHz clock. Should work with Uno, Nano, Duemilanove and 
others. Connect an IR LED to pin 12 with a suitable resistor in series 
and you're golden. Experiment with distance and LED frequency to get it 
just right. Some LEDs are very focused and offers only a narrow beam, so 
if you have the option, try to find one with a wide beam.
