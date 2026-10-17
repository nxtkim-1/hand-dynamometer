# 11 — Your tutorial: Git → electronics → firmware → data

This is your half of the project, start to finish. It doesn't depend on the printed parts at all, so you can do all of it while the mechanical design is still being decided.

Each part ends with **You should see** — don't move on until you do.

---

## Part 0 — What you need on the desk

**Parts:** load cell, HX711 board, Arduino Nano + USB cable, 4 jumper wires (female–female or male–female), heat-shrink tubing, 2 zip ties.

**Tools (DEN):** soldering iron + solder, wire strippers, flush cutters, multimeter, lighter or heat gun for the heat-shrink.

**Software (all free):** GitHub Desktop, Arduino IDE, Python 3, VS Code (optional but nice).

---

## Part 1 — Git and GitHub (30 min, once)

**What Git is:** a program that saves snapshots of a folder. Each snapshot ("commit") has a message saying what changed. You can go back to any snapshot. **GitHub** is the website that stores a copy so your partner and recruiters can see it.

1. Make an account at **github.com**. Use a professional username (e.g. `tkim-uw`).
2. Install **GitHub Desktop** (desktop.github.com) and sign in.
3. Unzip the project somewhere sensible, like `Documents/hand-dynamometer`.
4. GitHub Desktop → **File → Add local repository** → pick that folder. It says "this isn't a repository" → click **create a repository**. Name: `hand-dynamometer`.
5. Bottom-left box, type `Initial commit` → **Commit to main**.
6. Top bar → **Publish repository** → **untick "Keep this code private"** → Publish.
7. On github.com open your repo → **Settings → Collaborators → Add people** → your partner.

**You should see:** your project on github.com with the README showing on the front page.

### The four clicks you'll use forever

| When | Click |
|---|---|
| Before you start working | **Fetch origin**, then **Pull** if it appears |
| After you change something | Type a message → **Commit to main** |
| Right after committing | **Push origin** |

Good messages: `Solder cell to HX711, first continuity check`. Bad: `update`, `stuff`, `final2`.

---

## Part 2 — Install the software (30 min, once)

1. **Arduino IDE** — arduino.cc/en/software. Install.
2. **CH340 driver** — the ELEGOO Nano uses a CH340 USB chip. Windows usually installs it automatically; if the Nano doesn't appear later, search "CH340 driver" and install it from the chip maker's or ELEGOO's site. Mac needs it on older versions.
3. **HX711 library** — Arduino IDE → **Tools → Manage Libraries** → search `HX711` → install the one by **Bogdan Necula**.
4. **Python 3** — python.org. On Windows **tick "Add Python to PATH"** on the first installer screen.
5. Open a terminal in the project folder (Windows: in the folder, click the address bar, type `cmd`, Enter) and run:
   ```
   pip install -r software/requirements.txt
   ```

**You should see:** no red error text from pip.

---

## Part 3 — Test the Nano on its own (10 min)

Never connect anything to a board you haven't proven works.

1. Plug the Nano into your laptop.
2. Arduino IDE → **Tools → Board → Arduino AVR Boards → Arduino Nano**.
3. **Tools → Processor → ATmega328P (Old Bootloader)**. (ELEGOO clones almost always need "Old Bootloader".)
4. **Tools → Port** → pick the one that appeared when you plugged it in.
5. **File → Examples → 01.Basics → Blink** → click the **→ Upload** arrow.

**You should see:** "Done uploading" and a small LED on the Nano blinking once a second.

| If | Then |
|---|---|
| No port appears | Different USB cable (charge-only cables don't work), or install the CH340 driver |
| Upload fails / "not in sync" | Switch Processor between "Old Bootloader" and plain "ATmega328P" |

---

## Part 4 — What you're about to wire (5 min read)

The load cell is a metal bar with four tiny **strain gauges** glued on. When the bar bends — by less than a hair's width — their electrical resistance changes very slightly. They're wired in a pattern called a **Wheatstone bridge**, which turns that change into a voltage.

That voltage is tiny: about **10 thousandths of a volt** at the full 100 kg. The Nano can't read anything that small. So the **HX711** sits in between: it amplifies the signal 128× and converts it into a 24-bit number the Nano can read over two wires.

```
Load cell ──4 wires──> HX711 ──4 wires──> Nano ──USB──> laptop
 (tiny voltage)       (amplify + digitize)   (read + send)   (log + plot)
```

---

## Part 5 — Solder headers onto the HX711 (15 min)

HX711 boards usually come with a loose strip of pins. You need them for the jumper wires.

**If you've never soldered:** watch one 5-minute "how to solder header pins" video first. The rules: iron hot (~350 °C), touch the iron to the **pad and the pin at the same time** for two seconds, then feed solder into the joint — not onto the iron. A good joint is shiny and shaped like a small volcano.

1. Push the header strip into the 4 holes on the **VCC / SCK / DT / GND** side, long pins on the bottom.
2. Hold it straight with Blu-Tack or a breadboard.
3. Solder one pin, check it's straight, then the other three.

**You should see:** four shiny cone-shaped joints, no solder bridging two pins.

---

## Part 6 — Solder the load cell to the HX711 (30 min)

This is the most fragile part of the whole build. Go slowly.

1. Cut four pieces of heat-shrink, about 15 mm each. **Slide one onto each cell wire now** — push them well back from the end so the iron's heat doesn't shrink them early. (Everyone forgets this once.)
2. Strip 3 mm of insulation off each cell wire. The wires are thin; strip gently.
3. Twist the strands and put a little solder on the tip ("tinning").
4. Solder each wire to its pad on the HX711:

   | Cell wire | HX711 pad |
   |---|---|
   | **Red** | **E+** |
   | **Black** | **E−** |
   | **Green** | **A+** |
   | **White** | **A−** |

   **Check the label on your cell first** — a few sellers swap green and white. If the label says otherwise, follow the label.
5. Slide the heat-shrink over each joint and shrink it with a heat gun or by passing a lighter underneath (not touching).
6. **Zip-tie the four wires together about 30 mm from the cell body.** This takes the strain when the cable gets pulled, so it doesn't pull on the solder joints. Without it, these wires break — it's the most common failure in load-cell projects.

**Check with the multimeter (continuity / beep mode):** touch one probe to each coloured wire near the cell and the other to its HX711 pad. Each should beep. Touch red to black pads — should **not** beep.

---

## Part 7 — Wire the HX711 to the Nano (5 min)

Four jumper wires:

| HX711 | Nano |
|---|---|
| **VCC** | **5V** |
| **GND** | **GND** |
| **DT** | **D3** |
| **SCK** | **D2** |

Double-check VCC and GND before plugging in. Reversed power can kill the HX711.

---

## Part 8 — First signal: GATE G1 (15 min)

> Ready-made test sketch: `firmware/hx711_bench_test/hx711_bench_test.ino` (pins DT = D3, SCK = D2, 115200 baud). Breadboard layout: `images/breadboard_test.png`.

1. Plug in the Nano.
2. **File → Examples → HX711 → HX711_basic_example**.
3. **Important:** near the top of that example are two lines setting the pins. Change them to match your wiring:
   ```cpp
   const int LOADCELL_DOUT_PIN = 3;
   const int LOADCELL_SCK_PIN = 2;
   ```
   The library's example may use them the other way round. If you skip this, nothing works and nothing tells you why.
4. Upload. **Tools → Serial Monitor**. Set the baud (bottom-right dropdown) to the number in the example's `Serial.begin(...)` line — usually 57600.
5. Lay the cell flat. Hold one end firmly on the table, press down on the other end with your thumb.

**You should see:** a number printing repeatedly, which changes when you press and returns when you let go.

| If | Then |
|---|---|
| "HX711 not found" / nothing | DT and SCK swapped in the code vs. your wiring; or VCC/GND not connected — multimeter across VCC and GND on the HX711 should read ~5 V |
| Number never changes | A+ or A− not connected, or a cell wire broken — redo the continuity check |
| Numbers jump around wildly | Loose jumper wire; wiggle each one while watching |
| Changes in the "wrong" direction | Fine — that's fixed in software with `SIGN` later |

**This is the most important moment of the project.** Take a photo of the screen. Commit: `First signal from load cell`.

---

## Part 9 — The real firmware (45 min)

> The four steps below are written out as complete, commented sketches in `firmware/tutorial/` (step1 to step4), each with a "Check" and a "Try" line. Type each one yourself into `firmware/my_firmware/`, get it working, and commit it that day.

Now write your own version, in four steps. Test each before the next.

**Step 1 — print time.** New sketch (File → New):
```cpp
void setup() { Serial.begin(115200); }
void loop()  { Serial.println(millis()); delay(100); }
```
Upload, Serial Monitor at **115200**. You should see numbers climbing by ~100.

**Step 2 — read the raw sensor.**
```cpp
#include "HX711.h"
HX711 scale;
void setup() {
  Serial.begin(115200);
  scale.begin(3, 2);          // DT pin, SCK pin
}
void loop() {
  if (scale.is_ready()) Serial.println(scale.read());
}
```
You should see big numbers (hundreds of thousands) that change when you press.

**Step 3 — zero it.** Add a variable that stores the reading at startup, and subtract it:
```cpp
long offset = 0;
// in setup(), after scale.begin:
//   offset = scale.read_average(20);
// in loop():
//   Serial.println(scale.read() - offset);
```
Now it should sit near **0** at rest and go up (or down) when pressed.

**Step 4 — the full version.** Open `firmware/grip_firmware/grip_firmware.ino`. It's steps 1–3 plus:

| Line | What it does |
|---|---|
| `SIGN` | Flips the direction if pressing makes the number go negative |
| `COUNTS_PER_KG` | Converts raw counts to kg. Stays 1.0 until calibration |
| `doTare()` | Averages 20 readings (2 s) for a steady zero |
| The `t` command | Type `t` in the Serial Monitor to re-zero any time |
| The print lines | Output one CSV line: `time,raw,net,kg` |

Compare it with yours. Upload `grip_firmware.ino`. In Serial Monitor at 115200 you should see:
```
# tared
# hand_dynamometer_v1
t_ms,raw,net,force_kg
5123,8431022,12,12.000
5223,8431018,8,8.000
```
Press the cell. If `net` goes **negative**, change `const int SIGN = 1;` to `-1` and upload again.

Commit: `Firmware v1 running on hardware`.

---

## Part 10 — Log it on the laptop (20 min)

1. **Close the Arduino Serial Monitor.** Only one program can use the USB port at a time — this is the most common "it doesn't work" in this step.
2. Find your port name: in Arduino IDE, Tools → Port. Windows looks like `COM3`; Mac like `/dev/cu.usbserial-XXXX`.
3. In a terminal in the project folder:
   ```
   python software/logger.py COM3 --plot
   ```
4. Press the cell. A live graph follows your hand. Ctrl+C to stop.

**You should see:** a new file `session_<date>_<time>.csv`. Open it in Excel. The `pc_time_s` column should go up by about 0.1 each row — that's 10 readings per second.

Commit the CSV into `data/`: `First logged session`.

---

## Part 11 — Write it in the build log

Open `docs/06_build_log.md` and add:

```
### 2026-09-30 — [your name]
Soldered cell to HX711 (red E+, black E−, green A+, white A−), strain relief added.
Continuity checked. Library example: first signal (photo). Wrote firmware in 4 steps;
v1 running, SIGN = __. Logger at ~10 Hz confirmed. Next: calibration after assembly.
```

Commit and push.

---

## Where your part goes next

Everything above is done before the printed parts exist. When they arrive:

1. Unsolder nothing — the cell bolts into the printed parts with its wiring attached.
2. Help assemble (`docs/03_assembly.md`).
3. Calibration (`docs/04_calibration.md`) — you run `calibrate.py`, check `COUNTS_PER_KG` is about **43,000**, and paste it into the firmware.

That number going into the firmware is the moment the device starts reading real kilograms.
