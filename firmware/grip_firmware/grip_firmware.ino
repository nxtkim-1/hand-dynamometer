// Hand Dynamometer — firmware v1.0
// Board:   Arduino Nano / Uno (ATmega328P)
// Library: "HX711" by Bogdan Necula  (Arduino IDE -> Library Manager -> search "HX711")
//
// Serial output, 115200 baud, one CSV line per sample (~10 per second):
//     t_ms,raw,net,force_kg
//   raw      = value read from the HX711
//   net      = raw - zero offset (sign-corrected)
//   force_kg = net / COUNTS_PER_KG
//
// Serial commands (send a single character):
//     t   re-zero (tare). Make sure nothing is touching the handle.

#include "HX711.h"

// ---- Pins ---------------------------------------------------------
const int PIN_DOUT = 3;   // HX711 DT
const int PIN_SCK  = 2;   // HX711 SCK

// ---- Calibration --------------------------------------------------
// Counts per kilogram. Expect roughly 43000 for a 100 kg CZL601 at 2.0 mV/V.
// Leave at 1.0 until calibrate.py has been run,
// then paste the printed value here and re-upload.
const float COUNTS_PER_KG = 1.0;

// If squeezing makes 'net' go NEGATIVE, change this to -1.
const int SIGN = 1;
// -------------------------------------------------------------------

HX711 scale;
long offset = 0;

void doTare() {
  offset = scale.read_average(20);   // ~2 s at 10 samples/s
  Serial.println("# tared");
}

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DOUT, PIN_SCK);    // gain 128 on channel A (default)
  while (!scale.is_ready()) {
    delay(10);
  }
  doTare();
  Serial.println("# hand_dynamometer_v1");
  Serial.println("t_ms,raw,net,force_kg");
}

void loop() {
  // --- commands
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 't' || c == 'T') {
      doTare();
    }
  }

  // --- one line per new sample
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
