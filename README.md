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
  data from the original Timex software) - set up unit tests
* Work on the protocol documentation

More specific work:

* Implement phone number type/letter support


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

I have implemented the above protocol on an Arduino with hopes of being 
able to both turn it into a replacement adapter for the original software 
and to use it with my library. Currently, it implements the protocol as 
far as I can tell, but since it adds its own delays it will probably not 
work too well with the original software. I might explore this further in 
the future.

Hardware wise, you need an Arduino with ATmega328 (168 would probably 
work too) with 16 MHz clock. Should work with Uno, Nano, Duemilanove and 
others. Connect an LED to pin 12 (maybe with a suitable resistor in 
series) and that's it. Experiment with distance and light frequency to get 
it just right. Some LEDs are very focused and offers only a narrow beam, 
so if you have the option, try to find one with a wide beam.

As for the LED, I have tried a few different types ranging from IR to 
blue, from classic low-intensity red to modern cold white, and from what 
I can tell, the watch receives well on all of them. The only difference 
is in how close, how perpendicular, and how aligned the watch needs to 
be. If it is too close, the receiver seems to saturate and nothing is 
received.

What ultimately worked best for me was to use a high-intensity white LED 
without a resistor and shine it onto a surface. That way, the angle and 
position of the watch didn't matter as much.
