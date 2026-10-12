# 06 — Build log and schedule

**Started:** Friday, September 25, 2026
**Target:** device calibrated and report drafted by **Sunday, November 8, 2026**
**Buffer:** November 9–22 for slippage, then exams.

## How to use this file

Every time you do anything on the project, add an entry at the bottom. Date, who, what you did, what happened, what's next. Two lines is fine. Photos go in `images/` and get linked. This file *is* your engineering notebook, and it's what proves you ran a process rather than just producing an object.

Commit it every time you edit it. `git commit -m "log: printed fit coupon, cell bolts on"` — done.

## Schedule

| Week | Dates | Person A (mechanical) | Person B (software) | Gate |
|---|---|---|---|---|
| 1 | Sep 18–21 | Check DEN Sensors (Force). Order CZL601 100 kg parallel-beam cell + HX711, Nano, 2x M6×35 and 2x M6×30 bolts + 4 washers, M6 stop. Book printer. | Install Arduino IDE + Python. Run `logger.py fake`. Run `calibrate.py` on the example data. Read the firmware. | Parts ordered. |
| 1b | on arrival | Measure cell (P1–P5 in `08_verification_checklist.md`). Edit CAD. Run it. Print fit coupon; bolt cell on. | — | **G0: fit coupon passes. Only then print the frame.** |
| 2 | Sep 22–28 | Print fit coupon. Bolt cell on. Wire cell to HX711. Bench test with the library example. | Set up GitHub repo (see 07). Both commit. Write `fake` calibration session and test analysis end to end. | **G1: a number changes on screen when the cell is pressed.** |
| 3 | Sep 29–Oct 5 | Print frame + carrier + tray. | Firmware uploaded; `logger.py` on real hardware; confirm sign. | Parts printed. |
| 4 | Oct 6–12 | Assemble. Three clearance checks. Set stop bolt. Weigh calibration masses. | First real squeeze logged and plotted. | **G2: assembled device reads a squeeze.** *(Oct 12 is Thanksgiving — plan around it.)* |
| 5 | Oct 13–19 | **Calibration session** (both). 3 runs. Verification mass. | Run `calibrate.py`. Paste constant into firmware. | **G3: calibrated; verification error recorded.** |
| 6 | Oct 20–26 | Noise, drift, creep sessions. | Process all characterization data. Plots. | Characterization table complete. |
| 7 | Oct 27–Nov 2 | 30-s holds, both people, both hands. Photos of everything. | `analyze_hold.py` on all four. Hold plots. | Four hold plots. |
| 8 | Nov 3–8 | Write report sections 1–3, 6. | Write sections 4–5, 7. README results table. Demo video. | **G4: report drafted, README complete, repo public.** |

**The only gate that decides the project is G1.** If pressing the cell doesn't change a number by September 28, stop everything else and get help in person — DEN staff, a TA, an upper-year.

## Fallbacks (decided now, so there's no arguing later)

| If | Then |
|---|---|
| Cell is dead on arrival | Borrow from DEN Sensors (Force), or reorder — costs a week |
| Frame print fails twice | Print at 0.3 mm layers, or print the frame in two halves and bolt (ask before doing this) |
| No PETG | PLA, same settings, note it in limitations |
| No calibration weights | Water in containers, weighed on the DEN scale |
| Hysteresis > 2 % after clearance checks | Report it with root cause. Do not hide it. |
| One person unavailable a week | The other continues; the interface contract means nothing blocks |
| Behind at week 6 | Cut creep test and one hold subject. Keep calibration and report. |

## Entries

### 2026-09-25 — both
Project defined. Requirements written (docs/01).

First load cell choice was wrong and is recorded here deliberately. We specified a TAL220-family 100 kg straight bar (80 x 12.7 x 12.7 mm) and designed the whole frame around it. Checking availability before ordering showed that form factor only exists up to about 50 kg — a 12.7 mm aluminium section cannot carry 100 kg — and the 80-200 kg variants are alloy steel and unavailable at Canadian retail. The obvious substitute is also a trap: most "50 kg load cells" on Amazon are 34 x 34 mm half-bridge bathroom-scale sensors with three wires.

Cell re-specified as the CZL601 / CZL601AC 100 kg single-point parallel beam: 130 x 30 x 22 mm, 2x M6 threaded holes per end, 2.0 mV/V, 405 ohm in / 350 ohm out, class C2, safe overload 120 kg (docs/00).

That forced an architecture change. Stacking the grip above a 130 mm cell would have given a 175 x 250 mm frame footprint, unprintable on a 220 x 220 bed. The carrier now reaches over the cell's top and hangs back DOWN beside it, so grip and cell share a height band. Frame footprint is 160 x 170 mm — smaller than the previous design despite a much larger cell.

A 15 mm calibration tab was added above the carrier arm. Working through the z ranges, it is the only band where a hanging cord clears the cell, the carrier plate, the arm and the palm wall. The CAD now asserts those clearances at build time.

Mount uses locating ledges plus bolt slots (8-26 and 28-50 mm from each end face) so supplier variation in hole position does not matter. Expected sensitivity ~43,000 counts/kg as a wiring sanity check. All four parts regenerate watertight; software tested end to end with `logger.py fake`.

Next: check DEN Sensors (Force), order parts, book the printer.

### 2026-10-12 — Thomas (measured), Claude (drafted the log and drawings)
**Step 1 of the build: measure the real parts before editing any CAD.** Calipers from the DEN. Photos with the dimensions written on them are in `images/photos/`; the cleaned-up drawing is `images/measured_load_cell.png`.

![Load cell as measured](../images/measured_load_cell.png)

#### Load cell — what the calipers say

Source key: **M** = measured with calipers (Thomas's photos). **D** = derived by Claude from measured numbers. **P** = read off the photo by Claude, not measured. **?** = still unknown.

| Quantity | Value | Source | Note |
|---|---|---|---|
| Overall length | 130.00 mm | M | |
| Width | **40.00 mm** | M | spec in docs/00 said 30 |
| Thickness (load direction) | 22.00 mm | M | |
| End block length | 33.00 mm | M | left block; right assumed identical |
| Holes per end | **3** (one on the centreline, two side by side) | M | spec said 2 |
| Single hole: end face to near edge | 21.44 mm | M | |
| Single hole: far edge to block inner end | 5.00 mm | M | |
| Hole edge to cell side edge | 16.67 mm | M | |
| Hole opening diameter (centred on the width) | about 6.7 mm | D | 16.67 + 6.6 + 16.67 ≈ 40, so the hole is centred to within about 0.1 mm.  40 − 2 × 16.67; also 33 − 21.44 − 5.00 = 6.56, so the readings agree to 0.1 mm |
| Single hole centre from the end face | about 24.8 mm | D | 21.44 + 6.67 / 2 |
| Pair: gap between the two holes (edge to edge) | 7.94 mm (7.95 on the right end) | M | read as the gap, Claude's interpretation |
| Pair: centre spacing | about 14.6 mm | D | 7.94 + 6.67 |
| Pair: centre distance from the end face | **11.80 mm** | M | measured 16:50; the photo estimate (11.4) was 0.4 mm out |
| Bending zone (between the end blocks) | about 64 mm | D | 130 − 2 × 33 |
| Dumbbell slot: overall length | 32.60 mm | M | |
| Dumbbell slot: circle diameter | 12.8 mm | M | |
| Dumbbell slot: neck height | 6.50 mm | M | |
| Cable diameter | 5.13 mm | M | |
| Cable exit | end block at the right of the top photo | ? | which face, and 8.5 mm from which edge, is not clear from the photo |
| Thread | **M6** | M | an M6 bolt threads in by hand |
| Hole depth | **tapped all the way through** | M | so both ends can be bolted from opposite faces |
| Stamp | "2607021487, 100kg" and a downward arrow | | arrow = load direction |

#### Finding: the cell is not the one the CAD was built on

docs/00 and the CAD script assume a **130 × 30 × 22 mm cell with 2 × M6 per end**. The cell in hand is **130 × 40 × 22 mm with 3 holes per end** and 33 mm end blocks. It is the same family (100 kg parallel beam, same length and thickness) but a different part, so every dimension tied to width and hole position is wrong:

- The **fit coupon** has slots for 2 holes in line. It would not line up with a 3-hole pattern and it is 10 mm too narrow. It would have failed the G0 test; the measurement caught that before printing.
- The **pocket** in both halves is sized for a 30 mm wide cell. With a 40 mm cell and the current 3 mm gap all round, the far corner of the pocket sits 25.8 mm from the grip axis. The barrel's outer radius is 26.2 to 29.0 mm, so the wall would be **0.4 mm** at the top of the cell and 0.7 mm at the bottom. It would break through.
- The clamp zone is **33 mm** per end, not the 55 mm the CAD assumes, and the bolt windows (8–26 and 28–50 mm from each end) do not match the real holes (about 11.4 and 24.8 mm from the end).
- The bending zone is longer (64 mm), so the 3 mm clearance check needs new numbers.

Same lesson as the 2026-09-25 entry: the part has to be measured before the design is trusted. Costs nothing this time because nothing was printed.

#### Electronics

Nano measured with calipers on 2026-10-12 (second pass, 16:50). The HX711 is still the nominal 24 × 16 mm from a reference image and has **not** been measured. See `images/measured_electronics.png`.

| Quantity | Value | Source |
|---|---|---|
| Nano board length (PCB only) | **44.0 mm** | M |
| Nano length including the USB connector | **46.0 mm** | M |
| Nano width | **18.11 mm** | M (clone, reference drawing says 17.78) |
| USB connector height above the board | **3.8 mm** | M |
| Header pins | stick out **8 mm below and 8 mm above** the board | M |
| HX711 length × width | 24 × 16 mm | reference image, not measured |
| HX711 thickness, how it will be wired | | ? |

![Electronics](../images/measured_electronics.png)

**Nano vs the old pod:** the old pod bore is 46 mm across. A 44 × 18.11 board needs a bore of about 47.6 mm just to clear its corners (half the diagonal is 23.8 mm, the bore radius is 23.0), so the Nano **still does not fit** the pod as drawn.

**Wiring is undecided.** The HX711 has not been connected to anything yet. Options are: solder 4 short wires straight between HX711 and Nano (lowest, strongest); header pins plus Dupont jumper wires (quick for bench testing, about 14 mm tall and can shake loose); or Dupont wires for the bench test first and solder before the pod is closed.

#### Open questions (answers change the CAD)
1. **Cable exit:** which face does the cable leave from (it appears to be one of the long 130 × 22 side faces), how far is the hole from the end face, and how far from the mounting-hole face? The photo shows 8.5 mm and a smaller number that is hard to read.
2. HX711: real length, width and thickness.
3. Wiring method and whether there are any jumper wires or loose hookup wire on hand.
4. Bolts: three per end means **6** M6 bolts and washers; the BOM lists 4.

#### Design decision proposed (not yet applied)
Keep the 54–58 mm round barrel so the grip span does not change. Instead:
- cell width 40 mm, 3 holes per end, 33 mm clamp zone, 3 bolts per end;
- side clearance (across the 40 mm, where the cell does not move) reduced from 3 to 1.5 mm; clearance in the bending direction stays 3 mm;
- raise the minimum barrel radius from 26.2 to about 27.0 mm so the wall stays at 2.5 mm or more;
- re-run all build checks and print the new fit coupon first.

Status: nothing printed. The old fit coupon and halves are **not to be printed**; they are for the wrong cell.

Next: answer the five questions, measure the boards, then Claude updates `dynamometer_cad.py` and regenerates.
