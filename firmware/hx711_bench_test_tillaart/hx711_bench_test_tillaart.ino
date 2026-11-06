// HX711 bench test for Rob Tillaart's "HX711" library (gate G1).
// Wiring: HX711 GND -> Nano GND, VCC -> 5V, DT -> D3, SCK -> D2
// Serial Monitor at 115200 baud.
// Pass: the number jumps by tens of thousands when you press the cell
// (about 43,000 counts per kg) and comes back when you let go.
// Library: "HX711" by Rob Tillaart (Library Manager).

#include "HX711.h"

const int DT_PIN  = 3;   // HX711 DT
const int SCK_PIN = 2;   // HX711 SCK
HX711 scale;

void setup() {
  Serial.begin(115200);
  scale.begin(DT_PIN, SCK_PIN);                  // data pin first, then clock pin
  Serial.println("starting...");
}

void loop() {
  if (scale.is_ready()) {
    Serial.println(scale.read());                // raw counts
  } else {
    Serial.println("HX711 not found: check DT, SCK, VCC, GND");
  }
  delay(100);
}
