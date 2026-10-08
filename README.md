# Hand Dynamometer — a 3D-printed grip-strength meter with a calibration report

A handheld grip-strength instrument: a barrel-shaped handle split into two halves around a **CZL601 100 kg load cell**, read by an **HX711** amplifier and an **Arduino Nano**, logged to a laptop. Calibrated against known masses through the same load path as a real squeeze.

![Assembled](images/final_assembled.png)

## How it works

The grip is split lengthwise. The **grey palm half** bolts to the load cell's bottom end; the **black finger half** bolts to its top end. A 3 mm seam keeps them apart everywhere, so when you squeeze, **all of the force has to pass through the load cell.**

![Section](images/final_section.png)

![Drawing](images/final_drawing.png)

Full explanation of every feature, and how the design was arrived at: **[`docs/12_design.md`](docs/12_design.md)**.

## Why

Grip strength is a validated clinical measure — a diagnostic criterion for sarcopenia (EWGSOP2: < 27 kg men, < 16 kg women), and in the PURE study of ~140,000 people it predicted mortality better than systolic blood pressure. The clinical standard device costs several hundred dollars and reports one number; this one logs the whole force–time curve at 10 Hz.

**Educational and non-diagnostic. Not a medical device.**

## Results

*Fill in from `docs/05_calibration_report.md`.*

| Quantity | Measured | Load cell spec |
|---|---|---|
| Calibrated range | 0 – __ kg | 100 kg rated |
| Sensitivity | ______ counts/kg | ~43,000 expected |
| Max non-linearity | __.___ % FS | ±0.03 % FS comprehensive |
| Hysteresis | __.___ % FS | — |
| Repeatability (3 runs) | __.___ % FS | — |
| Creep, 20 kg / 30 min | __.__ % | ±0.023 % FS / 30 min |
| **Verification error, unseen mass** | **__._ %** | target ≤ 2 % |

## Build it

| Step | Doc |
|---|---|
| The load cell — buy, check, measure | `docs/00_load_cell.md` |
| Electronics and firmware, start to finish | `docs/11_firmware_tutorial.md` |
| Printing at the Rapid Prototyping Centre | `docs/02_printing.md` |
| Assembly | `docs/03_assembly.md` |
| Calibration | `docs/04_calibration.md` |
| Report template | `docs/05_calibration_report.md` |
| Day-by-day plan | `docs/09_daily_plan.md` |
| Verification checklist | `docs/08_verification_checklist.md` |

**Print the fit coupon first** and bolt your load cell to it before printing the halves.

## What's in the repo

```
cad/        dynamometer_cad.py   the whole design, parametric; regenerates every part and checks it
            render_final.py      the renders in images/
            draw_final.py        the dimensioned drawing
            output/              STL + STEP per part, assembly.step
            output/print_ready/  STLs ready for Bambu Studio — don't rotate them
            archive/             earlier design iterations
firmware/   grip_firmware/       Arduino sketch
software/   logger.py, calibrate.py, analyze_hold.py
docs/       everything above
images/     renders, drawings, and your photos
```

## Parts and cost

`docs/bom.csv`. About **$65** to buy (load cell, HX711, Nano, four M6 × 25 bolts) plus **~$20** of printing. Tools are borrowed from the DEN.

## Team

- **[Name]** — electronics, firmware, software, analysis
- **[Name]** — mechanical, printing, assembly, calibration

## License

Code: MIT. Hardware design files and documentation: CC BY 4.0.
