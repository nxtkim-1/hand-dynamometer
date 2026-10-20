// STEP 1 — hello, serial
// Goal: prove the Nano runs your code and talks to the laptop.
//
// New ideas
//   setup()  runs once when the board powers up or resets.
//   loop()   runs forever, over and over.
//   Serial   the USB link to the laptop. Both sides must use the same speed (baud).
//   millis() milliseconds since the board started. It's an unsigned long:
//            int on a Nano is only 16 bits and would overflow after 32 seconds.
//
// Check: Serial Monitor at 115200 baud shows a number every 100 ms that keeps climbing.
// Try:   change delay(100) to delay(500). What happens to the gap between numbers?
//        Open and close the Serial Monitor: the count restarts from 0. Opening the port
//        RESETS the Nano. Remember this - it matters a lot in step 3.

void setup() {
  Serial.begin(115200);          // 115200 bits per second
  Serial.println("step 1: hello");
}

void loop() {
  unsigned long t = millis();
  Serial.println(t);
  delay(100);                    // wait 100 ms; the board does nothing else meanwhile
}
