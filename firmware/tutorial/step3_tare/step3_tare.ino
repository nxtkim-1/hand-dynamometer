// STEP 3 — zero it (tare)
// Goal: 0 means "nothing is pressing". The raw number at rest is not zero - every
// cell has an offset - so measure it at startup and subtract it from every reading.
//
// New ideas
//   a function      doTare() is code with a name, so you can call it from more than one place.
//   a global        'offset' lives outside every function, so setup() and loop() both see it.
//   averaging       read_average(20) takes 20 readings (about 2 s) and averages them.
//                   One reading is noisy; 20 gives a steadier zero.
//   waiting safely  if the HX711 is missing, is_ready() never becomes true. Printing
//                   "waiting" tells you where it is stuck instead of a silent screen.
//
// IMPORTANT: hands off the cell while it tares. And remember step 1 - opening the
// Serial Monitor (or starting logger.py) resets the board, so it tares again.
// If something is resting on the cell at that moment, that weight becomes your "zero".
//
// Check: about 0 at rest (+/- a few hundred), large numbers when pressed, back near 0 when released.
// Try:   press while it tares, then let go. What does "net" show now, and why?

#include "HX711.h"

const int PIN_DOUT = 3;
const int PIN_SCK  = 2;

HX711 scale;
long offset = 0;

void doTare() {
  offset = scale.read_average(20);
  Serial.print("# tared, offset = ");
  Serial.println(offset);
}

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DOUT, PIN_SCK);
  while (!scale.is_ready()) {
    Serial.println("# waiting for HX711 - check DT, SCK, VCC, GND");
    delay(500);
  }
  doTare();
}

void loop() {
  if (scale.is_ready()) {
    long raw = scale.read();
    long net = raw - offset;
    Serial.println(net);
  }
}
