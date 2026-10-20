# 10 — Software, and how to actually own these skills

## The honest framing first

This repo arrived finished. If you print the STLs, upload the firmware, run the scripts and ship it, you will have a working device and **almost no transferable skill** — and an interviewer will find that out in about ninety seconds, because the questions are never "did it work?" They are *"why is the load cell vertical?"*, *"why slots instead of holes?"*, *"what does your fit residual tell you?"*

So treat the repo as a **reference implementation**, not a deliverable. The plan below has you rebuild each piece yourself and check your version against mine. It costs maybe eight extra hours across eight weeks, and it's the difference between "I built a dynamometer" and being able to defend every decision in it.

---

## The stack

| Software | Cost | Used for | Which files | Learning curve |
|---|---|---|---|---|
| **Git + GitHub Desktop** | free | Version control, collaboration, the public artifact | everything | 1 h |
| **Arduino IDE** | free | Writing and flashing firmware | `firmware/grip_firmware/` | 2 h |
| **C++** (Arduino subset) | — | The firmware language | `grip_firmware.ino` | 3 h |
| **Python 3** | free | All acquisition and analysis | `software/` | you have this |
| **pyserial** | free | Reading the USB stream | `logger.py` | 1 h |
| **NumPy** | free | Least-squares fitting, statistics | `calibrate.py` | 2 h |
| **Matplotlib** | free | Every plot in the report | all three scripts | 3 h |
| **CadQuery** | free | Parametric CAD — all printed parts | `cad/dynamometer_cad.py` | 6 h |
| **Bambu Studio** | free | STL → printer job for the RPC's Bambu P1S/P2S | `cad/output/print_ready/` | 2 h |
| **FreeCAD** *(optional)* | free | Opening the STEP files graphically | `cad/output/*.step` | 1 h |
| **trimesh** | free | Checking meshes are watertight, renders | `render_previews.py` | 1 h |

Everything is free and cross-platform. No licences, no student accounts, nothing to expire.

---

## Part 1 — Git and GitHub

**What it does for you:** a public record of eight weeks of steady work, which is the single most credible thing a first-year can show.

**Learn it by:** `docs/07_github_guide.md`, then just using it. Commit at the end of every session.

**Exercise:** edit one line of the README, commit with a real message, push. Have your partner pull it. Then deliberately both edit `06_build_log.md` on the same day and resolve the conflict. Ten minutes, and conflicts stop being scary forever.

**Interview line:** *"Every design decision is in the commit history with its reasoning."*

---

## Part 2 — Arduino and C++

**What it does:** reads the HX711 ten times a second, subtracts the tare, scales to kilograms, prints a CSV line.

### Rebuild it yourself

Don't copy `grip_firmware.ino`. Build up to it in four steps, testing each:

1. **Blink.** File → Examples → Basics → Blink. Proves board and cable.
2. **Print a counter.** In `loop()`, `Serial.println(millis());`. Proves serial.
3. **Read the sensor.** Use the HX711 library example. Get a raw number changing.
4. **Write your own.** From scratch, with the library: tare on startup, subtract the offset, divide by a constant, print `t_ms,raw,net,force_kg`, hold ~10 Hz.

Then diff yours against mine. Where they differ, work out who is right — sometimes it'll be you.

**Then extend it.** Two small features that force real understanding:
- Add a serial command `c` that prints the current `COUNTS_PER_KG`.
- Blink the onboard LED once per sample so you can see the rate without a screen.

**What you'll actually learn:** `setup()`/`loop()` structure, `Serial` I/O, non-blocking timing with `millis()` instead of `delay()`, calling a library, and integer vs. float behaviour. That's 90 % of embedded work at this level.

---

## Part 3 — Python: pyserial

**Exercise — write a 20-line logger before you look at mine:**

```python
import serial, csv, time
ser = serial.Serial("COM3", 115200, timeout=1)
time.sleep(2)                      # the Arduino resets when the port opens
with open("out.csv", "w", newline="") as f:
    w = csv.writer(f)
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        parts = line.split(",")
        if len(parts) == 4:
            w.writerow(parts)
            print(parts[3])
```

Get that working, then read `logger.py` and ask what each extra thing is for: why `time.sleep(2)`, why `f.flush()`, why the `--fake` mode, why the last-2-seconds statistics.

**The three things that bite everyone:** only one program can hold a serial port (close the Arduino Serial Monitor), the first line you receive is usually a fragment, and port names differ by OS.

---

## Part 4 — NumPy and Matplotlib

**Exercise — do the calibration fit by hand before running mine.** Given eight `(mass, counts)` pairs:

```python
import numpy as np, matplotlib.pyplot as plt
m = np.array([...]); c = np.array([...])
slope, intercept = np.polyfit(m, c, 1)
resid = c - (slope*m + intercept)
print(slope, np.max(np.abs(resid))/slope)      # counts/kg, worst error in kg
plt.plot(m, resid, "o"); plt.axhline(0); plt.show()
```

That's genuinely the whole of `calibrate.py`'s mathematics. Everything else in that file is bookkeeping for hysteresis and repeatability.

**Then answer, from your own plot:** if the residuals are randomly scattered you have noise; if they bow (positive in the middle, negative at the ends) you have real nonlinearity. Which do you have? Being able to read a residual plot is a small skill that reads as surprisingly senior.

---

## Part 5 — CadQuery (the most valuable one)

This is the steepest and the most transferable. Parametric, code-driven CAD is how production mechanical design increasingly works, and almost no first-year has touched it.

### The ladder — do these in order

**Rung 1 (30 min):** Open `dynamometer_cad.py`. Change `GRIP_SPAN` from 50 to 55. Re-run. Open the new STL. Notice that the carrier moved and the bolt-length printout changed. *That* is what parametric means.

**Rung 2 (1 h):** Add a second calibration hook hole 20 mm below the first. You'll need to find `hole_y()` and copy one line. Re-run, confirm it's there.

**Rung 3 (2 h):** From a blank file, model a simple L-bracket: 60 × 40 × 4 mm, two Ø5 holes in each leg, a fillet on the inside corner. Export an STL.

```python
import cadquery as cq
b = (cq.Workplane("XY").box(60, 40, 4)
       .faces(">Z").workplane().pushPoints([(-20, 0), (20, 0)])
       .hole(5))
cq.exporters.export(b, "bracket.stl")
```

**Rung 4 (3 h):** Model something you actually want — a phone stand, a headphone hook, a cable clip. Print it. This is the rung where it stops feeling like copying.

**Rung 5:** Now re-read `dynamometer_cad.py` top to bottom. It will look ordinary.

**Resources:** the CadQuery docs "Examples" page is the best reference; the API is small. Search the CadQuery Google Group for anything odd.

### Should you learn FreeCAD or Fusion too?

Eventually. Many co-op postings name SolidWorks or Fusion 360 specifically, and they're click-and-drag rather than code. But the *concepts* — sketch, extrude, fillet, constraint, assembly — transfer directly from what you're doing here, so you'll pick one up in a weekend afterwards. Open `cad/output/assembly.step` in FreeCAD once, just so you can say you've used it and understand what STEP is.

---

## Part 6 — Slicing

**Exercise:** slice `fit_coupon_print.stl` three ways and record estimated time and filament for each: (a) 3 walls / 20 % infill, (b) 5 walls / 40 %, (c) 5 walls / 40 % rotated 90°. Then explain why (c) would be structurally worse.

**What to actually understand:** layer height vs. time, walls vs. infill for a part loaded in bending, why orientation determines strength in printed parts, and what supports cost you. Four ideas, and they cover most of what an FDM print needs from you.

---

## What each piece is worth on a resume

| Skill | Where it shows up |
|---|---|
| Parametric CAD | mechanical design, medical devices, robotics — and it's rare in first-years |
| Strain gauges and bridge sensors | every force, pressure and torque measurement in medtech |
| Calibration and measurement uncertainty | QA, metrology, test engineering, R&D |
| Embedded C++ | firmware, instrumentation, robotics |
| Python data analysis | essentially every engineering role now |
| Git | table stakes, and its absence is noticed |
| DFM for 3D printing | product design, prototyping, makerspace credibility |

---

## A suggested rebuild schedule

Fold these into the daily plan without adding weeks:

| Week | Rebuild exercise | Extra time |
|---|---|---|
| 1 | Git conflict exercise | 20 min |
| 2 | Firmware from scratch, steps 1–4 | 2 h |
| 2 | CadQuery rungs 1–2 | 1.5 h |
| 3 | 20-line logger before reading mine | 1 h |
| 3 | Slicer comparison exercise | 45 min |
| 4 | Fit by hand with `np.polyfit` | 1 h |
| 5 | CadQuery rungs 3–4 | 5 h |
| 6 | Add the two firmware commands | 1 h |

About **12 hours** total. It's the highest-return time in the whole project.

---

## The question to keep asking

For every file in this repo: **could I rewrite this from scratch, and can I say why it is the way it is?**

If yes for all of them, the project is genuinely yours and the interview takes care of itself. If no for some, those are exactly the files to rebuild next.
