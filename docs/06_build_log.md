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
