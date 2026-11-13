// Hand Dynamometer — firmware v1.0 for Rob Tillaart's "HX711" library
// Board:   Arduino Nano (ATmega328P)
// Library: "HX711" by Rob Tillaart (Arduino IDE -> Library Manager -> search "HX711")
//
// Serial output, 115200 baud, one CSV line per sample (~10 per second):
//     t_ms,raw,net,force_kg
//   raw      = value read from the HX711
//   net      = (raw - zero offset), sign-corrected so a squeeze is positive
//   force_kg = net / COUNTS_PER_KG   (equals net until you calibrate)
//
// Serial commands (send a single character):
//     t   re-zero (tare). Make sure nothing is touching the handle.
//
// Only begin(), is_ready() and read() are used from the library, so the averaging
// is written out here and nothing depends on library details that differ between versions.

#include "HX711.h"

// ---- Pins ---------------------------------------------------------
const int PIN_DOUT = 3;   // HX711 DT
const int PIN_SCK  = 2;   // HX711 SCK

// ---- Calibration --------------------------------------------------
// Counts per kilogram. PROVISIONAL: 42952 is the datasheet-based estimate for a 100 kg CZL601
// (2.0 mV/V, 5 V excitation, gain 128). It is NOT measured, expect +/-5-10 %.
// After G3 (hanging known masses) replace it with the fitted value from software/calibrate.py.
const float COUNTS_PER_KG = 42952.0;

// Your cell read NEGATIVE when pressed on the bench, so this starts at -1.
// If a squeeze of the assembled grip still shows a negative 'net', change it to 1.
const int SIGN = -1;
// -------------------------------------------------------------------

HX711 scale;
long offset = 0;

// Average of n readings (blocks until each one is ready).
long readAverage(int n) {
  double sum = 0;
  for (int i = 0; i < n; i++) {
    while (!scale.is_ready()) {
      delay(1);
    }
    sum += scale.read();
  }
  return (long)(sum / n);
}

void doTare() {
  offset = readAverage(20);          // about 2 s at 10 samples/s
  Serial.println("# tared");
}

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DOUT, PIN_SCK);    // data pin first, then clock pin
  doTare();
  Serial.println("# hand_dynamometer_v1");
  Serial.println("# calibration=estimated (datasheet, about +/-10 %)");   // change to measured after G3
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
    long  raw = (long)scale.read();
    long  net = SIGN * (raw - offset);
    float kg  = net / COUNTS_PER_KG;

    Serial.print(millis()); Serial.print(',');
    Serial.print(raw);      Serial.print(',');
    Serial.print(net);      Serial.print(',');
    Serial.println(kg, 3);
  }
}
