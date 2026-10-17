// STEP 4 — the full version: CSV for the laptop, kilograms, and a tare command
// Goal: output logger.py can save and calibrate.py can use. This equals
// firmware/grip_firmware/grip_firmware.ino v1.0.
//
// New ideas
//   CSV            one line per sample: t_ms,raw,net,force_kg. Lines starting with '#'
//                  are comments that logger.py skips.
//   float          a number with decimals, for kilograms.
//   COUNTS_PER_KG  counts per kilogram. Leave it at 1.0 until calibration (G3);
//                  calibrate.py prints the real value (expect about 43,000).
//   SIGN           if squeezing makes 'net' go negative, set this to -1.
//   reading input  Serial.available() says a character arrived; Serial.read() takes it.
//                  Sending 't' re-zeros without resetting the board.
//
// Check: the header line, then lines like 12345,8301122,-4,-4.000 about 10 times a second.
//        Send t in the Serial Monitor: "# tared" appears and net goes back to about 0.
// Try:   set COUNTS_PER_KG to 43000.0 and press with one finger - roughly how many kg?

#include "HX711.h"

const int PIN_DOUT = 3;
const int PIN_SCK  = 2;

const float COUNTS_PER_KG = 1.0;   // replace after calibration
const int   SIGN = 1;              // -1 if squeezing reads negative

HX711 scale;
long offset = 0;

void doTare() {
  offset = scale.read_average(20);
  Serial.println("# tared");
}

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DOUT, PIN_SCK);
  while (!scale.is_ready()) {
    Serial.println("# waiting for HX711 - check DT, SCK, VCC, GND");
    delay(500);
  }
  doTare();
  Serial.println("# hand_dynamometer_v1");
  Serial.println("t_ms,raw,net,force_kg");
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 't' || c == 'T') {
      doTare();
    }
  }

  if (scale.is_ready()) {
    long  raw = scale.read();
    long  net = SIGN * (raw - offset);
    float kg  = net / COUNTS_PER_KG;

    Serial.print(millis()); Serial.print(',');
    Serial.print(raw);      Serial.print(',');
    Serial.print(net);      Serial.print(',');
    Serial.println(kg, 3);
  }
}
