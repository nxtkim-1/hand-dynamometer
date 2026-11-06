// HX711 bench test WITHOUT any library (gate G1).
// Talks to the HX711 directly: wait for DT to go LOW, clock out 24 bits, 1 extra pulse = channel A, gain 128.
// Wiring: HX711 GND -> Nano GND, DT -> D3, SCK -> D2, VCC -> 5V
// Serial Monitor at 115200 baud. Pass: the number moves by tens of thousands when the cell is pressed
// (about 43,000 counts per kg) and comes back when released.

const int DT_PIN  = 3;   // HX711 DT  -> D3
const int SCK_PIN = 2;   // HX711 SCK -> D2

// Returns true and puts the reading in 'value' if the HX711 answered within 1 s.
bool readHX711(long &value) {
  unsigned long start = millis();
  while (digitalRead(DT_PIN) == HIGH) {          // HIGH = no new reading yet
    if (millis() - start > 1000) return false;
  }
  long v = 0;
  noInterrupts();                                 // SCK must not stay HIGH longer than 60 us
  for (int i = 0; i < 24; i++) {
    digitalWrite(SCK_PIN, HIGH);
    delayMicroseconds(1);
    v = (v << 1) | digitalRead(DT_PIN);           // most significant bit first
    digitalWrite(SCK_PIN, LOW);
    delayMicroseconds(1);
  }
  digitalWrite(SCK_PIN, HIGH);                    // 25th pulse: next reading on channel A, gain 128
  delayMicroseconds(1);
  digitalWrite(SCK_PIN, LOW);
  interrupts();
  if (v & 0x800000L) v |= 0xFF000000L;            // 24-bit two's complement -> negative long
  value = v;
  return true;
}

void setup() {
  Serial.begin(115200);
  pinMode(DT_PIN, INPUT);
  pinMode(SCK_PIN, OUTPUT);
  digitalWrite(SCK_PIN, LOW);                     // SCK held HIGH > 60 us powers the HX711 down
  Serial.println("starting (no library)...");
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
