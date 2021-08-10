/* Implementation of transcoder, behaving closely to the Notebook
 * Adapter. Compatible with the original Timex software.
 *
 * This code should work on any Arduino with an ATmega328 at 16 MHz,
 * such as Duemillanove, Uno, Nano, and others.
 *
 * The transmission is paced by the transmission rate between PC and
 * Blaster being 9600 baud. Inter-package delay can be done on either PC
 * or blaster side. The first case works better with the Python software
 * and I believe the latter with the original software. (TODO: verify)
 */

/* If TURBO_MODE is defined, the blasting will be faster. It works fine
 * most of the time, but the slower speed will probably be more reliable
 * in worse lighting conditions.
 */
#define TURBO_MODE

#define LEDPIN 13 /* Onboard LED pin */
#define IRLED 12 /* Comm. LED pin */
#define CTSPIN 11 /* Connect to CTS to reset when using the original software */
#define TESTPIN 10 /* Connect to GND to get a continuous stream of sync bytes */


/* =========== DATA TRANSCODER FUNCTIONS ========================= */

/* Start a timer which counts 1 each clock cycle. When it reaches
 * (hicnt*256)+lowcnt, OCF1A is set. Call waitTimer() to wait until this
 * bit is set.
 */
inline void startTimer(int lowcnt, int hicnt)
{
	/* Set count mode and max count*/
	TCCR1A = 0;
	OCR1AH = hicnt;
	OCR1AL = lowcnt;

	/* Stop timer 1 */
	TCCR1B = 0;

	/* Zero out timer 1 */
	TCNT1 = 0;

	/* Reset overflow flag */
	TIFR1 = 2; /* OCF1A */

	/* Start timer with prescaler 1 */
	TCCR1B = 1;
}

/* Assembly would be preferred but we're a bit lax on timing requirements */
#define waitTimer() while ( !(TIFR1 & 0x02 ) ) /* OCF1A */


#ifdef TURBO_MODE
	/* These values are faster than the original software sends using the
	* CRT, but they seem to work most of the time. */

	/* Bit length */
	#define BITLEN_L 252
	#define BITLEN_H 1

	/* Bit interval */
	#define SPACELEN_L 206
	#define SPACELEN_H 28

	#define INTERBYTE_L 0
	#define INTERBYTE_H 180

	#define INTERBYTE_PACKAGE 25
#else
	/* Timing values based more on the CRT timings. */

	/* Bit length */
	/* 31.78 kHz => 16 MHz / 31.78 kHz ~= 508 counts (Approx 0.0318 ms bit length) */
	#define BITLEN_L 252
	#define BITLEN_H 1

	/* Bit interval */
	/* 31.47 kHz / (15-1) => 7118 counts (Approx 0.445 ms between bits, or 0.477 ms bit interval or 2098 baud) */
	#define SPACELEN_L 206
	#define SPACELEN_H 28

	/* Mostly a mode-up value that when combined with INTERBYTE_PACKAGE ends up with a sensible delay between packets */
	#define INTERBYTE_L 0
	#define INTERBYTE_H 220

	/* Number of times to repeat interbyte delay between packages */
	/* Set this to 0 for compatibility with original software */
	#define INTERBYTE_PACKAGE 45
#endif

bool past55sync;
bool pastAAsync;
unsigned int packetLeft;
bool transmitState;

void setupTranscode()
{
	past55sync = false;
	pastAAsync = false;
	packetLeft = 0;

	pinMode(IRLED, OUTPUT);
	digitalWrite(IRLED, LOW);
}

#define interPacketDelay() do {										\
		digitalWrite(LEDPIN, LOW);									\
		for (unsigned int ipd=0; ipd<INTERBYTE_PACKAGE; ipd++) {	\
			startTimer(INTERBYTE_L, INTERBYTE_H);					\
			waitTimer();											\
		}															\
		digitalWrite(LEDPIN, HIGH);									\
	} while (0);													\

void transcodeByte(unsigned char curbyte)
{
	if (curbyte != 0x55) {
		if (!past55sync) {
			/* Delay between 0x55-sync and 0xAA-sync - TODO: Test if this is necessary; doesn't seem to be. */
			//interPacketDelay();
		}
		past55sync = true;
		if (curbyte != 0xAA) {
			pastAAsync = true;
		}
	}

	if (pastAAsync) {
		/* Delay before each package */
		if (packetLeft <= 0) {
			/* Get new packet length. First byte of package is package length, including this length byte. */
			packetLeft = curbyte;
			interPacketDelay();
		}
		packetLeft--;
	}

	noInterrupts();
	/* Start bit */
	startTimer(BITLEN_L, BITLEN_H);
	digitalWrite(IRLED, HIGH);
	waitTimer();
	startTimer(SPACELEN_L, SPACELEN_H);
	digitalWrite(IRLED, LOW);
	waitTimer();

	/* Other bits */
	for (unsigned int b=0; b<8; b++) {
		startTimer(BITLEN_L, BITLEN_H);
		digitalWrite(IRLED, !(curbyte&0x01) );
		waitTimer();
		startTimer(SPACELEN_L, SPACELEN_H);
		digitalWrite(IRLED, LOW);
		curbyte>>=1;
		waitTimer();
	}
    interrupts();
}


/* ======= MAIN FUNCTIONS =============== */

void setup()
{
	Serial.begin(9600);

	pinMode(LEDPIN, OUTPUT);
	digitalWrite(LEDPIN, LOW);

	pinMode(CTSPIN, INPUT_PULLUP);
	pinMode(TESTPIN, INPUT_PULLUP);

	setupTranscode();

	transmitState = false;
}

void loop()
{
	unsigned char curbyte;

	/* If test pin is low, output sync bytes */
	if (!digitalRead(TESTPIN)) {
		transcodeByte(0x55);
		delay(2);
		return;
	}

	/* If CTS is pulled low, reset transmission state. This controls the
	 * power to the original device, so essentially resets it.
	 */
	if (!digitalRead(CTSPIN)) {
		setupTranscode();
	}

	/* Read byte if available */
	if (Serial.available()) {
		curbyte = Serial.read();
	} else return;

	/* If we're not in transmit state, handle commands.
	 * Else, transcode byte.
	 */
	if (!transmitState) {
		if (curbyte == 'x') {
			/* Knock knock */
			Serial.print('x');
		} else
		if (curbyte == '?') {
			/* Device query */
			Serial.print("M764");
			Serial.write((byte)0);
		}
		else
		if (curbyte == 'U') {
			/* Enter transmit state */
			transmitState = true;
			Serial.print('U');
		}
	} else {
		transcodeByte(curbyte);
		Serial.write(curbyte);
	}
}
