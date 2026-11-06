// HX711 bench test WITHOUT any library (gate G1).
// Wiring: HX711 GND -> Nano GND, VCC -> 5V, DT -> D3, SCK -> D2
// Serial Monitor at 115200 baud.
// Pass: the number jumps by tens of thousands when you press the cell
// (about 43,000 counts per kg) and comes back when you let go.

const int DT_PIN  = 3;   // HX711 DT
const int SCK_PIN = 2;   // HX711 SCK

void setup() {
  Serial.begin(115200);
  pinMode(SCK_PIN, OUTPUT);
  pinMode(DT_PIN, INPUT);
  digitalWrite(SCK_PIN, LOW);
  Serial.println("starting...");
}

// Returns true and fills 'out' if the HX711 answered within 1 second.
bool readHX711(long &out) {
  unsigned long t0 = millis();
  while (digitalRead(DT_PIN) == HIGH) {          // DT goes LOW when a reading is ready
    if (millis() - t0 > 1000) return false;
  }
  long value = 0;
  noInterrupts();                                // SCK must not stay HIGH too long
  for (int i = 0; i < 24; i++) {                 // 24 bits, most significant first
    digitalWrite(SCK_PIN, HIGH);
    delayMicroseconds(1);
    value = (value << 1) | digitalRead(DT_PIN);
    digitalWrite(SCK_PIN, LOW);
    delayMicroseconds(1);
  }
  digitalWrite(SCK_PIN, HIGH);                   // 25th pulse: next reading uses gain 128, channel A
  delayMicroseconds(1);
  digitalWrite(SCK_PIN, LOW);
  interrupts();
  if (value & 0x800000L) value |= 0xFF000000L;   // sign-extend the 24-bit number
  out = value;
  return true;
}

void loop() {
  long counts;
  if (readHX711(counts)) {
    Serial.println(counts);
  } else {
    Serial.println("HX711 not found: check DT, SCK, VCC, GND");
  }
  delay(100);
}
