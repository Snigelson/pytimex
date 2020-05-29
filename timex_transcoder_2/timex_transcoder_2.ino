/* Implementation which buffers all data before sending. See README. */

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


#define LEDPIN 13
#define IRLED 12

void setup()
{
  pinMode(LEDPIN, OUTPUT);
  digitalWrite(LEDPIN, LOW);
  pinMode(IRLED, OUTPUT);
  digitalWrite(IRLED, LOW);

  Serial.begin(9600);
}

/* 31.47 kHz => 16 MHz / 31.47 kHz = 508 counts (Approx .0318 ms bit length) */
#define BITLEN_L 0
#define BITLEN_H 2
//#define BITLEN_L 252
//#define BITLEN_H 1

/* 31.47 kHz / (15-1) => 7118 counts (Approx 0.445 ms between bits, or 0.477 ms bit interval or 2098 baud) */
#define SPACELEN_L 206
#define SPACELEN_H 28
//#define SPACELEN_L 206
//#define SPACELEN_H 27

/* 31.47 kHz / 68 (made up) => 34573 counts (approx 2.16 ms between bytes) */
/* Trying larger delay so that it sounds more like data from the PC. */
#define INTERBYTE_L 0
#define INTERBYTE_H 220
//#define INTERBYTE_L 13
//#define INTERBYTE_H 135

/* Number of times to repeat interbyte package between bytes */
#define INTERBYTE_BYTE 3

/* Number of times to repeat interbyte package between packages */
#define INTERBYTE_PACKAGE 45

void blastData(unsigned char* data, int datalen)
{
  unsigned char curbyte;
  unsigned int packetLeft = 0;
  bool past55sync = false;
  bool pastAAsync = false;

  /* Disable arduino interrupts (temporarily breaks delay, serial, ...) */
  noInterrupts();

  for (unsigned int i=0; i<datalen; i++) {
    curbyte = data[i];

    if (curbyte != 0x55) {
      if (!past55sync) {
        /* Delay between 0x55-sync and 0xAA-sync - Test if this is necessary. */
        digitalWrite(LEDPIN, LOW);
        for (unsigned int ipd=0; ipd<INTERBYTE_PACKAGE; ipd++) {
          startTimer(INTERBYTE_L, INTERBYTE_H);
          waitTimer();
          digitalWrite(LEDPIN, HIGH);
        }
      }
      past55sync = true;
      if (curbyte != 0xAA) {
        pastAAsync = true;
      }
    }

    if (pastAAsync) {
      /* Delay before each package */
      if (packetLeft <= 0) {
        /* First byte of package is package length, including this length byte */
        packetLeft = curbyte;
        
        digitalWrite(LEDPIN, LOW);
        for (unsigned int ipd=0; ipd<INTERBYTE_PACKAGE; ipd++) {
          startTimer(INTERBYTE_L, INTERBYTE_H);
          waitTimer();
        }
        digitalWrite(LEDPIN, HIGH);

      }
      packetLeft--;
    }

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

    /* Inter-byte delay */
    for (unsigned int ipd=0; ipd<INTERBYTE_BYTE; ipd++) {
      startTimer(INTERBYTE_L, INTERBYTE_H);
      waitTimer();
    }
  }

  /* Re-enable arduino interrupts */
  interrupts();

  digitalWrite(LEDPIN,HIGH);
}

void loop()
{
  size_t datalen;
  unsigned char* data;

  while (!Serial.available());
  datalen = (Serial.read()<<8)&0xFF00;
  while (!Serial.available());
  datalen += (Serial.read())&0x00FF;

  data=malloc(datalen);

  for (int i=0; i<datalen; i++) {
    while (!Serial.available());
    data[i] = Serial.read()&0xFF;
  }

  blastData(data, datalen);

  free(data);
}
