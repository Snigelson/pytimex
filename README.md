## pytimex - Timex Data Link watch library

Python libraries for generating and transmitting data to the Timex Data
Link series of watches using optical data tramsission, an Arduino
sketch fully able to replace the Notebook Adapter as well as work with
this library, and software for capturing and decoding packets from the
original software.

Currently, the protocol for the original Data Link (50 and 70) is
implemented fully, the 150 and 150s partially, and the Ironman
Triathlon is being worked on.

There is a guide [written by dfries]
(https://github.com/dfries/datalink_ironman/blob/github_submodules/datalink/70.txt)
on the Data Link packet encoding. This information was verified using the 
original software, and a few errors were corrected. The data was 
collected using the included script timex_notebook_adapter.py, which 
emulates the Timex Notebook Adapter and logs all bytes sent from the 
program. Much easier than getting it from the CRT!


## TODO

* Test everything more extensively (most tests so far have been
  comparing to data from the original Timex software)
* Work on the protocol documentation

More specific work:

* Implement phone number type/letter support
* Support for date format (model 150)
* Support for multiple numbers on one phone book entry
* Add "beeps" packet


## "Timex Notebook Adapter"

A device for sending data to the watch if you don't have access to a CRT 
monitor. Connected via serial port and powered by the CTS line. Initially 
responds to commands "x" (reply with "x", used for identification), "?" 
(reply with "M764\0", probably some kind of model name) and 0x55 (enter 
send mode, actually the first sync bytes sent). After 0x55 is received, 
all bytes are sent over the IR LED. To get back to the initial state, 
device power must be cycled. This is done by pulling CTS low for a few 
hundred milliseconds.

When a byte is sent to the adapter, it replies with the same byte to keep
things in sync.

Since I do not have access to an actual adapter, I have no way of
verifying the timings of the device. It's a safe bet, though, that they
will be very similar to those from the CRT. It is also possible the
data could be sent somewhat faster since it does not need to be phase
locked to the CRT refresh.


## The Blaster

Arduino code for the above protocol is available in `timex_transcoder`.
It works both with the Pyhton code, and with the original Timex software
using an RS232 to UART converter.

To use it you need an Arduino with ATmega328 (168 would probably work too)
with 16 MHz clock. Should work with Uno, Nano, Duemilanove and 
others. Connect a bright LED to pin 12 (maybe with a suitable resistor in 
series) and that's it.

Experiment with distance and intensity to get it just right. Some LEDs
are very focused and offers only a narrow beam, and might saturate the
receiver.

What ultimately worked best for me was to use a high-intensity white LED 
without a resistor and shine it onto a surface. That way, the angle and 
position of the watch didn't matter as much.
