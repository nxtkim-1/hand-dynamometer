// Hand Dynamometer — firmware v1.1 for Rob Tillaart's "HX711" library
// Board:   Arduino Nano (ATmega328P)
// Library: "HX711" by Rob Tillaart (Arduino IDE -> Library Manager -> search "HX711")
//
// Serial output, 115200 baud, one CSV line per sample (~10 per second):
//     t_ms,raw,net,force_kg
//   raw      = value read from the HX711
//   net      = (raw - zero offset), sign-corrected so a squeeze is positive
//   force_kg = net / counts_per_kg
//
// Start-up comment lines (the GripCheck website reads these):
//     # tared
//     # hand_dynamometer_v1.1
//     # counts_per_kg=42952.0
//     # sign=1
//     # calibration=estimated (datasheet, about +/-10 %)      or      # calibration=measured 2026-11-23
//
// Serial commands:
//     T            re-zero (tare). Nothing may touch the handle. Replies "# tared". (single character)
//     I            print the settings lines above again. (single character)
//     C <cpk> [YYYYMMDD]   save a measured counts_per_kg (from known masses), end with a newline.
//                          Replies "# saved counts_per_kg=..." then the settings lines.
//     S <1|-1>     save the direction, end with a newline. Replies "# saved sign=...".
//     R            back to the datasheet estimate and the default sign, end with a newline.
//
// The GripCheck website's Calibrate page sends C and S for you. Settings live in EEPROM, so they
// survive power-off and re-uploading this sketch.
//
// Only begin(), is_ready() and read() are used from the library, so the averaging
// is written out here and nothing depends on library details that differ between versions.

#include "HX711.h"
#include <EEPROM.h>

// ---- Pins ---------------------------------------------------------
const int PIN_DOUT = 3;   // HX711 DT
const int PIN_SCK  = 2;   // HX711 SCK

// ---- Defaults, used until a calibration is saved --------------------
// 42952 counts/kg is the datasheet estimate for a 100 kg CZL601 (2.0 mV/V, 5 V, gain 128), about +/-10 %.
const float DEFAULT_COUNTS_PER_KG = 42952.0;

// Which way the cell bends depends on the frame it sits in:
//   v3 barrel grip:      -1  (the bare cell read negative when pressed, verified 2026-11-12)
//   v4.2 Jamar frame:    +1  (a squeeze read negative with -1, reported 2026-11-23)
// The Calibrate page can change this without re-uploading (command S).
const int DEFAULT_SIGN = 1;

// Sane limits for a saved calibration (the datasheet value is 42952).
const float MIN_COUNTS_PER_KG = 10000.0;
const float MAX_COUNTS_PER_KG = 100000.0;
// -------------------------------------------------------------------

struct Settings {
  uint16_t magic;        // MAGIC when the block holds valid settings
  uint8_t  version;
  int8_t   sign;         // +1 or -1
  float    countsPerKg;
  uint8_t  measured;     // 1 = from known masses, 0 = datasheet estimate
  uint32_t calDate;      // YYYYMMDD of the calibration, 0 = unknown
};
const uint16_t MAGIC = 0x4743;   // "GC"
const uint8_t  SETTINGS_VERSION = 1;

HX711 scale;
long offset = 0;
Settings cfg;

char cmd[40];
uint8_t cmdLen = 0;

void useDefaults() {
  cfg.magic = MAGIC;
  cfg.version = SETTINGS_VERSION;
  cfg.sign = DEFAULT_SIGN;
  cfg.countsPerKg = DEFAULT_COUNTS_PER_KG;
  cfg.measured = 0;
  cfg.calDate = 0;
}

void loadSettings() {
  EEPROM.get(0, cfg);
  bool ok = cfg.magic == MAGIC && cfg.version == SETTINGS_VERSION && (cfg.sign == 1 || cfg.sign == -1) &&
            cfg.countsPerKg >= MIN_COUNTS_PER_KG && cfg.countsPerKg <= MAX_COUNTS_PER_KG;
  if (!ok) useDefaults();   // blank or old EEPROM: start from the datasheet estimate
}

void saveSettings() {
  EEPROM.put(0, cfg);       // put() only rewrites bytes that changed
}

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

void printDate(uint32_t d) {
  Serial.print(d / 10000);
  Serial.print('-');
  uint8_t m = (d / 100) % 100, day = d % 100;
  if (m < 10) Serial.print('0');
  Serial.print(m);
  Serial.print('-');
  if (day < 10) Serial.print('0');
  Serial.print(day);
}

void printSettings() {
  Serial.println("# hand_dynamometer_v1.1");
  Serial.print("# counts_per_kg=");
  Serial.println(cfg.countsPerKg, 1);
  Serial.print("# sign=");
  Serial.println(cfg.sign);
  if (cfg.measured) {
    Serial.print("# calibration=measured");
    if (cfg.calDate) {
      Serial.print(' ');
      printDate(cfg.calDate);
    }
    Serial.println();
  } else {
    Serial.println("# calibration=estimated (datasheet, about +/-10 %)");
  }
}

void runCommand() {
  cmd[cmdLen] = '\0';
  char *arg = cmd + 1;
  while (*arg == ' ') arg++;
  char c = cmd[0];

  if (c == 'C' || c == 'c') {
    char *end;
    float cpk = (float)strtod(arg, &end);
    if (end == arg || cpk < MIN_COUNTS_PER_KG || cpk > MAX_COUNTS_PER_KG) {
      Serial.println("# error counts_per_kg out of range (10000-100000)");
      return;
    }
    uint32_t date = strtoul(end, NULL, 10);
    if (date < 20000101UL || date > 20991231UL) date = 0;
    cfg.countsPerKg = cpk;
    cfg.measured = 1;
    cfg.calDate = date;
    saveSettings();
    Serial.print("# saved counts_per_kg=");
    Serial.println(cfg.countsPerKg, 1);
    printSettings();
  } else if (c == 'S' || c == 's') {
    long s = strtol(arg, NULL, 10);
    if (s != 1 && s != -1) {
      Serial.println("# error sign must be 1 or -1");
      return;
    }
    cfg.sign = (int8_t)s;
    saveSettings();
    Serial.print("# saved sign=");
    Serial.println(cfg.sign);
  } else if (c == 'R' || c == 'r') {
    useDefaults();
    saveSettings();
    Serial.println("# saved defaults");
    printSettings();
  } else {
    Serial.println("# error unknown command");
  }
}

void readCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (cmdLen == 0 && (c == 't' || c == 'T')) {          // single-character commands, as in v1.0
      doTare();
    } else if (cmdLen == 0 && (c == 'i' || c == 'I')) {
      printSettings();
    } else if (c == '\n' || c == '\r') {
      if (cmdLen > 0) runCommand();
      cmdLen = 0;
    } else if (cmdLen < sizeof(cmd) - 1) {
      cmd[cmdLen++] = c;
    }
  }
}

void setup() {
  Serial.begin(115200);
  loadSettings();
  scale.begin(PIN_DOUT, PIN_SCK);    // data pin first, then clock pin
  doTare();
  printSettings();
  Serial.println("t_ms,raw,net,force_kg");
}

void loop() {
  readCommands();

  // --- one line per new sample
  if (scale.is_ready()) {
    long  raw = (long)scale.read();
    long  net = cfg.sign * (raw - offset);
    float kg  = net / cfg.countsPerKg;

    Serial.print(millis()); Serial.print(',');
    Serial.print(raw);      Serial.print(',');
    Serial.print(net);      Serial.print(',');
    Serial.println(kg, 3);
  }
}
