// STEP 2 — read the raw sensor
// Goal: see the load cell respond. This is gate G1.
//
// New ideas
//   #include       pulls in a library: someone else's code for talking to the HX711 chip.
//   an object      'HX711 scale;' creates one HX711 you control with scale.something().
//   const int      a name for a number that never changes (pin numbers). Easier to read, can't be changed by mistake.
//   polling        is_ready() asks "do you have a new reading?" The HX711 makes 10 per second.
//                  We only read when it says yes, so the loop never sits waiting.
//   long           32-bit whole number. The HX711 gives 24-bit readings, too big for int.
//
// Wiring: HX711 DT -> D3, SCK -> D2, VCC -> 5V, GND -> GND (images/breadboard_test.png)
// Check: a steady number at rest that jumps by tens of thousands when you press the cell.
// Try:   press harder - does the change roughly double? Which direction does it move?

#include "HX711.h"

const int PIN_DOUT = 3;   // HX711 DT
const int PIN_SCK  = 2;   // HX711 SCK

HX711 scale;

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DOUT, PIN_SCK);   // gain 128 on channel A (the library's default)
  Serial.println("step 2: raw counts");
}

void loop() {
  if (scale.is_ready()) {
    long raw = scale.read();
    Serial.println(raw);
  }
}
