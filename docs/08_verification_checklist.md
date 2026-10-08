# 08 — Verification checklist

Print this. Tick as you go. Every requirement from `01_design_process.md` maps to one row, and every row maps to evidence you can point at.

**Build:** ____________  **Date:** ____________  **Checked by:** ____________

## Before printing

| # | Check | Method | Pass | Evidence |
|---|---|---|---|---|
| P1 | Cell is a full bridge (4 separate wires) | Count the wires | ☐ | photo |
| P2 | Cell measures 130 × 30 × 22 (±0.5) | Calipers | ☐ | recorded: ______ |
| P3 | Both ends confirmed M6 | Test-fit an M6 screw | ☐ | |
| P4 | Hole distances fall inside the slot windows | Calipers vs. 8–26 and 28–50 mm | ☐ | near ____, far ____ |
| P5 | CAD re-run with measured values | `python dynamometer_cad.py` | ☐ | console output saved |
| P6 | Fit coupon printed; cell sits on ledge, both bolts reach through slots | Physical test | ☐ | photo |

**Do not print the palm or finger halves until P1–P6 pass.**

## After assembly

| # | Requirement | Check | Pass | Evidence |
|---|---|---|---|---|
| A1 | R3 — both side seams clear, full length | Paper slides freely | ☐ | |
| A2 | R3 — top seam (dome) and bottom seam (base) clear | Paper slides freely | ☐ | |
| A3 | R3 — no wire crosses a seam | Visual | ☐ | |
| A4 | R4 — grip diameter ~58 mm at the fullest | Calipers | ☐ | measured ______ |
| A9 | Calibration cord hangs clear from the dome; zip tie around base pod only | Visual | ☐ | |
| A5 | Bolt heads flush in their counterbores | Run a finger over them | ☐ | |
| A6 | R7 — no conductive path to the user | Multimeter, outside surface → any circuit node | ☐ | open ☐ |
| A7 | Device feels rigid; no click, scrape or creak | Hard squeeze | ☐ | |
| A8 | Reading returns to zero after release | Logger | ☐ | |

## After calibration

| # | Requirement | Target | Measured | Pass |
|---|---|---|---|---|
| C1 | Fitted `COUNTS_PER_KG` plausible | ~43,000 ±30 % | | ☐ |
| C2 | R1 — calibrated range | ≥ 30 kg | 0 – ____ kg | ☐ |
| C3 | R2 — verification error, unseen mass | ≤ 2 % | ____ % | ☐ |
| C4 | Non-linearity | report it (cell 0.03 % FS comprehensive) | ____ % FS | ☐ |
| C5 | Hysteresis | report it (cell 0.03 % FS comprehensive) | ____ % FS | ☐ |
| C6 | Repeatability across 3 runs | report it (cell 0.03 % FS comprehensive) | ____ % FS | ☐ |
| C7 | Noise floor, 1σ over 60 s | report it | ____ kg | ☐ |
| C8 | Zero drift over 30 min | < 0.5 kg | ____ kg | ☐ |
| C9 | Creep at ~20 kg over 30 min | report it (cell 0.023 % FS / 30 min) | ____ % | ☐ |
| C10 | Intercept after tare | near zero | ____ counts | ☐ |

**A failed row is not a failed project.** Record the number and diagnose the cause in the report's limitations section. "Hysteresis measured 0.9 % FS against a cell spec of 0.05 %; the difference is frame compliance, confirmed by a dial indicator on the wall top during loading" is a stronger result than a silent pass.

## Software

| # | Check | Method | Pass |
|---|---|---|---|
| S1 | R5 — sample rate ≥ 10 Hz, no gaps | Timestamp diff in a logged CSV | ☐ |
| S2 | Tare command works | Send `t`, reading goes to ~0 | ☐ |
| S3 | `analyze_hold.py` metrics correct | Run on a synthetic curve with known peak | ☐ |
| S4 | CSV opens in Excel / pandas | Open one | ☐ |
| S5 | `logger.py fake` runs with no hardware | Run it | ☐ |

## Repository

| # | Check | Pass |
|---|---|---|
| G1 | R11 — README complete, results table filled | ☐ |
| G2 | All STLs and the CAD script committed | ☐ |
| G3 | Firmware committed with the final `COUNTS_PER_KG` | ☐ |
| G4 | Raw calibration and session CSVs committed | ☐ |
| G5 | Calibration report committed with photos | ☐ |
| G6 | Build log has entries across all 8 weeks | ☐ |
| G7 | LICENSE present; repo public | ☐ |

## Sign-off

Device is calibrated over 0–____ kg with a verification error of ____ %, and all clearance checks pass as of ____________.

Signed: ____________  ____________
