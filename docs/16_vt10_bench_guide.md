# 16 - Bench guide: proof load (VT-09) and calibration (VT-10) of v4.2

Print this page and fill it in by hand at the bench. About 75 minutes; two people is easier.
Protocol and acceptance criteria: `docs/15_calibration_v4_2.md` and report GC-TR-002 section 8.1.

**Every "expected" value below is a prediction from the datasheet factor (42,952 counts/kg, about ±10 %) and
an assumed hanger set of 1.0 kg. It is a sanity check while you work, never a result.** The result is
whatever the logger records.

Hard limit: **34.0 kg total on the strap**, hanger included. Feet never under the hanger.

---

## 0. Take with you

- [ ] Device, laptop with this repo, USB cable
- [ ] Plates 2.5, 5, 10, 25, 35, 45, 50 lb; hanger; carabiner; flat strap about 25 mm wide (webbing, not rope)
- [ ] Two wooden blocks (2×4 offcuts)
- [ ] Scale reading to 35 kg or more (DEN), pen, this sheet

## 1. Weigh everything (15 min)

Weigh on the scale, write kg to 0.01. Use these numbers, not the stamped ones.

| Item | Stamped | Weighed (kg) |
|---|---|---|
| Hanger + strap + carabiner (H) | — | |
| Plate 2.5 lb | 1.13 kg | |
| Plate 5 lb | 2.27 kg | |
| Plate 10 lb | 4.54 kg | |
| Plate 25 lb | 11.34 kg | |
| Plate 35 lb | 15.88 kg | |
| Plate 45 lb | 20.41 kg | |
| Plate 50 lb | 22.68 kg | |

Check: H + 50 + 10 + 5 lb plates must be **under 34.0 kg**. If not, skip the 65 lb steps.

## 2. Firmware and device check (10 min)

1. Arduino IDE → open `firmware/grip_firmware_tillaart/grip_firmware_tillaart.ino` → confirm `const int SIGN = 1;`.
2. Tools → Board: **Arduino Nano**. Processor: **ATmega328P** (if upload fails: **ATmega328P (Old Bootloader)**). Port: your COM port. **Upload**.
3. **Close the Arduino IDE** (only one program can hold the port).
4. `python software/check_device.py` → fix any FAIL. Note the COM port it found: COM____
5. In the browser, if you ever pressed **Reverse direction** on the GripCheck website, press **Undo reverse**.

| Check | Expected | Seen | OK |
|---|---|---|---|
| check_device.py | READY (WARNs for estimated calibration and 10 Hz are normal) | | ☐ |
| Samples per second | about 10 | | ☐ |

## 3. Rig (10 min)

```
           wooden block              wooden block
        ===[ top arm of frame ]========[ ... ]===
                 |  finger bar  |   <- strap loops over its BACK face, middle-finger height
                 |  palm bar    |   <- palm bar points DOWN
        ===[ bottom arm of frame ]=====[ ... ]===
                   \          /
                    strap legs     (outside the palm bar, touching nothing)
                        |
                    carabiner
                        |
                     HANGER   + plates
```

1. Turn the device so the **palm bar points down** and the finger bar is above it.
2. Rest the frame on the two blocks by its arms. **Never clamp the printed frame.**
3. Strap over the **finger bar's back face** at middle-finger height, both legs down outside the palm bar,
   clipped to the carabiner. **Hanger not on yet.**
4. Strap touches only the finger bar. Anything else it touches steals force from the cell.

## 4. Start the logger ONCE

```
cd C:\Users\nxtho\.t3\projects\gripdynamometer\data
python ..\software\logger.py COM7 --label g3_v42
```

(Use your COM port.) It prints `elapsed s   net = …   force = … kg` twice a second.
**Write down the elapsed seconds at each step.** Never stop and restart it until the end: opening the port
reboots the Nano and re-zeroes it.

Logger started at clock time: __:__  File name printed: session_______________________.csv

## 5. The run

Each step: lower the old load gently → hang the new one → stop the swing → **hands off** → wait 10 s →
write the elapsed seconds and the `net` you see.

**Live self-check:** divide `net` by the total mass (kg). That number should be **nearly the same at every step**
(within about 0.5 %), even if it is not 42,952. If it drifts up or down as the load grows, something is rubbing.

Expected `net` assumes H = 1.0 kg. If your H is different, add **about 43,000 counts per kg** of difference.

### a. Rest and direction (2 min)

| Step | Load | Hold | Expected `net` | Seen | Logger s |
|---|---|---|---|---|---|
| a | nothing (strap only), hands off | 60 s | 0 ± 100; jitter about ±70 | | |
| b | hanger only | 20 s | **positive**, about 43,000 (39,000–47,000) | | |

**If b reads negative: stop.** The sign or the rig is upside down. Do not load further.

### b. Proof load: VT-09 (12 min)

Hang, hold 30 s, unload to hanger only for 20 s, write the zero.

| Step | Load on hanger | Total kg (H+plates) | Hold | Expected `net` (±10 %) | Seen | Back at hanger only (expected 43,000 ± 200) | Logger s |
|---|---|---|---|---|---|---|---|
| P1 | 10 | | 30 s | 238,000 (214,000–262,000) | | | |
| P2 | 25 | | 30 s | 530,000 (477,000–583,000) | | | |
| P3 | 45 | | 30 s | 920,000 (828,000–1,012,000) | | | |
| P4 | 50 + 10 + 5 | | **5 min** | 1,309,000 (1,178,000–1,440,000) | at 10 s: | at 5 min: | |

P4 creep (5 min reading − 10 s reading): expected **under about 500 counts**. Seen: ______

**Stop immediately** at a crack, white stress mark, creak, visible bending of an arm, or a hanger-only reading
that does not come back within ±200 counts. Write what happened. Do not continue on a damaged part.

### c. Calibration runs: VT-10 (about 25 min)

| Step | Load on hanger | Total kg | Expected `net` (±10 %) | Run 1 up | s | Run 2 up | s |
|---|---|---|---|---|---|---|---|
| 0 | hanger only | | 43,000 (39,000–47,000) | | | | |
| 1 | 10 | | 238,000 (214,000–262,000) | | | | |
| 2 | 25 | | 530,000 (477,000–583,000) | | | | |
| 3 | 45 | | 920,000 (828,000–1,012,000) | | | | |
| 4 | 50 + 5 | | 1,114,000 (1,003,000–1,226,000) | | | | |
| 5 | 50 + 10 + 5 | | 1,309,000 (1,178,000–1,440,000) | | | | |

| Step | Load on hanger | Expected vs. the same load going up | Run 1 down | s | Run 2 down | s |
|---|---|---|---|---|---|---|
| 4 | 50 + 5 | about 1,000–6,000 counts **higher** | | | | |
| 3 | 45 | about 1,000–6,000 higher | | | | |
| 2 | 25 | about 1,000–6,000 higher | | | | |
| 1 | 10 | about 1,000–6,000 higher | | | | |
| 0 | hanger only | within ±200 of the up value | | | | |

Run 1 vs. run 2 at the same step: expected within about **600–4,000 counts**.

### d. Check load and final zero (2 min)

| Step | Load | Total kg | Expected `net` (±10 %) | Seen | Logger s |
|---|---|---|---|---|---|
| C | **35 lb plate alone** on hanger | | 725,000 (652,000–797,000) | | |
| Z | remove everything, hands off, 60 s | 0 | 0 ± 200 | | |

Press **Ctrl+C**. The logger prints the file name. Check the file is in `data\`.

## 6. Results you should expect after the fit

These are what `calibrate.py` will report. Values outside the range are findings to explain, not a failed project.

| # | Quantity | Expected | Pass / investigate |
|---|---|---|---|
| C1 | Fitted counts/kg | 38,700–47,200 | outside ±30 % of 42,952: rig or wiring fault |
| C2 | Calibrated range | 0 to about 30 kg | pass if ≥ 30 kg |
| C3 | Check-load error | under 1 % | pass ≤ 2 % |
| C4 | Nonlinearity | 0.1–0.5 % of range | investigate above 1 % |
| C5 | Hysteresis | 0.1–0.5 % of range | above 1 %: something rubbing |
| C6 | Repeatability | 0.05–0.3 % | above 0.5 %: strap moved between runs |
| C7 | Curvature | straight line adequate | — |
| C8 | Zero return | ±50–150 counts | pass within ±200 |
| C9 | Creep, 5 min at about 30 kg | under about 500 counts | — |
| C10 | Rest noise (1 s.d.) | 20–40 counts (0.5–1 g) | above 100: wiring or power noise |

## 7. Troubleshooting at the bench

| You see | Most likely | Do |
|---|---|---|
| `net` negative on the hanger | SIGN or rig upside down | Stop; check `SIGN = 1` was uploaded and the palm bar points down |
| Every step about 10–30 % low | Strap or finger part touching the frame | Re-route the strap; paper-slide the gaps |
| counts/kg rises or falls with load | Rubbing, or the strap slides along the bar | Fix and restart that run |
| Reading jumps to near 0 mid-session | The Nano rebooted (port re-opened, cable knocked) | Note the time; restart the whole run from step a |
| Value keeps creeping for minutes | Warm-up drift or a part settling | Wait at step a until the rest value is steady before loading |
| Logger prints nothing | Port busy | Close Arduino IDE / Serial Monitor; check the COM number |

## 8. Send

- The file path `data\session_…_g3_v42.csv`
- A photo of this filled-in sheet (weighed masses and logger seconds)
- Photo P3: the rig, one wide shot and one strap close-up

From these, each step's mean is extracted from the logger file, `data/calibration_points.csv` is built,
and `python software/calibrate.py data/calibration_points.csv` gives C1–C10.
