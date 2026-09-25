# 00 — The load cell

Every dimension in this project derives from this part. Read this before buying anything.

## The part

**CZL601 / CZL601AC family single-point (parallel beam) load cell, 100 kg.**

This is the part that is actually purchasable at 100 kg. It is the one sold on Amazon.ca as "100kg Parallel Beam Electronic Load Cell", usually around $20–25, frequently bundled with an HX711.

| | |
|---|---|
| Dimensions | **130 × 30 × 22 mm** |
| Mounting | **2 × M6 threaded holes at each end** |
| Material | anodised aluminium alloy |
| Lead | 4-wire, ~250 mm |
| Wire colours | red = EXC+, black = EXC−, **green = SIG+**, white = SIG− *(confirm against your cell's own label)* |
| Ingress | IP65 |
| Design intent | off-centre load, platform up to 250 × 250 mm |

### Electrical and accuracy specifications

| Parameter | Value |
|---|---|
| Rated output | **2.0 ± 0.2 mV/V** |
| Accuracy class | C2 |
| Comprehensive error | ±0.03 % FS |
| Creep | ±0.023 % FS / 30 min |
| Zero output | ±1.5 % FS |
| Input impedance | 405 ± 10 Ω |
| Output impedance | 350 ± 3 Ω |
| Excitation | 5–12 VDC |
| Zero temperature effect | ±0.029 % FS / 10 °C |
| Sensitivity temperature effect | ±0.025 % FS / 10 °C |
| Temperature compensation range | −10 to +40 °C |
| Operating temperature range | −20 to +60 °C |
| Safe overload | 120 % FS (**120 kg**) |
| Limit overload | 150 % FS (**150 kg**) |

**These are your comparison targets.** In the calibration report you measure your whole instrument's nonlinearity, hysteresis, repeatability and creep, then compare against this column. Anything worse came from your frame, your mounting or your reference masses — not the sensor. Working out which is the most interesting analysis in the project.

## Why not the small 80 × 12.7 mm bar

An earlier version of this design used the TAL220 straight bar. That was a mistake worth recording: **the slim bar form factor only goes to about 50 kg.** A 12.7 mm square aluminium section physically cannot carry 100 kg, and the 80–200 kg variants in that family are alloy steel and do not reach consumer retail in Canada. SparkFun's Canadian listings stop at 5 kg and 10 kg.

Be careful with the obvious workaround, too: nearly every "50 kg load cell" sold on Amazon is a **34 × 34 × 8 mm half-bridge** bathroom-scale sensor sold in packs of four. Three wires, not four. Those need four cells wired together plus bridge completion resistors, and they are not usable here.

**Rule: four separate wires, or it's the wrong part.**

## Why 100 kg and not 50

Adult grip strength commonly reaches 45–55 kgf and strong individuals exceed 70. A 50 kg cell has a safe overload of only 60 kg, which a hard squeeze can pass. At 100 kg the safe overload is 120 kg, which no hand will reach.

Resolution is not the trade-off you might expect. At 2.0 mV/V with 5 V excitation, full scale is 10 mV; the HX711 at gain 128 spans ±19.53 mV across 24 bits, giving roughly **43,000 counts per kilogram**. HX711 noise at 10 SPS is tens of counts, so the cell resolves about a gram. Your own grip varies by 2–4 kg between consecutive squeezes — thousands of times larger. **The sensor is nowhere near being your limiting factor**, so take the overload headroom.

## The one number to check after calibration

`calibrate.py` prints a fitted `COUNTS_PER_KG`. The CAD script prints the expected value (~43,000 for a 100 kg cell at 2.0 mV/V).

| Result | Meaning |
|---|---|
| Within ±30 % | Wiring and gain are right |
| About half | Possibly on HX711 channel B (gain 32), or a 1.0 mV/V cell |
| Roughly double | Possibly a 50 kg cell |
| Negative | Signal wires swapped — set `SIGN = -1` in the firmware |

This check catches wiring mistakes that a beautifully linear calibration would otherwise hide.

## A note on bridge impedance

This cell is a 350 Ω bridge, drawing about 12 mA from the HX711's on-board regulator — roughly three times what a 1000 Ω cell draws. The HX711 handles it; this combination is what the vast majority of hobby scale kits use. Worth knowing, not worth worrying about.

## Buying it

Search Amazon.ca for **"100kg load cell HX711"** or **"parallel beam load cell 100kg"**. Check DEN → Parts → Sensors (Force) first; if they stock one it's free.

Before adding to cart, confirm from the listing:

- **Four separate wires.** Three means a half bridge.
- Dimensions stated as roughly 130 × 30 × 22 mm.
- Two threaded holes at each end (some variants show three — the slots accommodate either).
- Ideally a stated mV/V. If it isn't listed, you'll determine it during calibration.

## Measure yours before printing

With calipers, record:

1. Bar length (nominal 130.0)
2. Width and thickness (nominal 30 × 22)
3. Thread size at each end — test-fit an M6 screw
4. Distance from each end face to each hole centre
5. How many holes at each end

Then open `cad/dynamometer_cad.py`, set `CELL_L`, `CELL_W`, `CELL_T`, `BOLT_FIXED`, `BOLT_FREE`, and confirm your measured hole distances fall inside `SLOT_NEAR` (8–26 mm) and `SLOT_FAR` (28–50 mm). Widen those windows if not. Re-run the script.

**Why the slots exist:** hole positions vary between suppliers and the published drawings are bitmaps that cannot be measured precisely. Rather than depend on a number we cannot verify, the design locates the cell with a **ledge** that its end face butts against, and passes the bolts through **slots**. Any spacing in the covered range assembles. This is why the fit coupon takes 50 minutes instead of a reprint of the 12-hour frame.

## Which end goes where

Both ends are M6 on this cell, so either works. If yours differs, put the **larger thread at the bottom** against the frame — that end carries the higher bending moment.

## Handling

- Don't over-torque the mounting bolts. Snug plus a quarter turn. Crushing the body distorts the flexures and adds permanent zero offset.
- Clamp only the end regions. The flexure is the machined cutout in the middle and must be left completely free.
- Don't drop it or use it as a lever.
- The four lead wires are thin and break at the solder joint. Zip-tie them within 30 mm of the body before doing anything else.
