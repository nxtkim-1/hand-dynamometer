// HX711 bench test: prints raw counts so you can see the load cell respond (gate G1).
// Wiring (breadboard, see images/breadboard_test.png):
//   HX711 GND -> Nano GND, DT -> D3, SCK -> D2, VCC -> 5V
// Serial Monitor at 115200 baud. Pass: the number moves by tens of thousands
// when the cell is pressed (about 43,000 counts per kg) and comes back when released.
// Library: "HX711 Arduino Library" by Bogdan Necula.
// Note: the library's own example uses DT on D2 and SCK on D3 - the opposite of this wiring.

#include "HX711.h"
const int DT_PIN  = 3;   // HX711 DT  -> D3
const int SCK_PIN = 2;   // HX711 SCK -> D2
HX711 scale;

void setup() {
  Serial.begin(115200);
  scale.begin(DT_PIN, SCK_PIN);
  Serial.println("starting...");
}

void loop() {
  if (scale.wait_ready_timeout(1000)) {
    Serial.println(scale.read());          // raw counts
  } else {
    Serial.println("HX711 not found: check DT, SCK, VCC, GND");
  }
  delay(100);
}
