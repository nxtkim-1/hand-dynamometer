# hand-dynamometer: project instructions for Claude Code

3D-printed grip-strength dynamometer (CZL601 100 kg load cell, HX711, Arduino Nano) plus **GripCheck**,
a Python app that runs a standardized grip test and compares results with Dodds et al. (2014) norms.
Educational project, not a medical device.

**Who owns what:** Thomas Kim owns hardware, CAD, firmware and the calibration docs (`cad/`, `firmware/`,
`docs/`, `software/`). Samuel Koo owns the app (`webapp.py`, `grip_test.py`, `metrics.py`, `filters.py`,
`quality.py`, `report.py`, `web/`, `tests/`). Change the other person's code only through a pull request
that they review.

Current status and the to-do list: @docs/HANDOFF.md

## Layout
- `webapp.py` + `web/`: GripCheck in the browser (Flask). `grip_test.py`: same protocol in the terminal.
- `metrics.py`, `filters.py`, `quality.py`, `grip_compare.py`, `report.py`: analysis, shared by both front ends.
- `firmware/grip_firmware_tillaart/`: **the firmware in use** (Rob Tillaart's HX711 library).
  `firmware/grip_firmware/` is the same program for Bogdan Necula's library. `firmware/tutorial/`: teaching steps.
- `software/calibrate.py`: fits COUNTS_PER_KG from known masses. `software/logger.py`: CSV logger.
- `cad/`: CadQuery models (`compact_base_draft.py` is the released v3 box). Onshape holds the native models.
- `docs/06_build_log.md`: dated build log. `docs/04_calibration.md`: calibration procedure.

## Commands
```bash
pip install -r requirements.txt
python -m pytest -q                      # must stay green (56 tests)
python webapp.py                         # simulated data, http://localhost:8000
python webapp.py --device                # real device, port found automatically (--port COM7 to force)
python software/check_device.py          # one-minute device health check (Windows: check_device.bat)
GRIPCHECK_DEMO=1 python webapp.py        # behave like the public Render demo
python software/calibrate.py data/calibration_points.csv
```
On Windows PowerShell, set the env var with `$env:GRIPCHECK_DEMO="1"`.

## Hardware facts (do not guess these)
- Wiring: HX711 VCC→5V, GND→GND, DT→D3, SCK→D2. Serial 115200 baud.
- Firmware prints `t_ms,raw,net,force_kg` (about 10 lines/s). `t` or `T` re-zeroes. Lines starting `#` are comments.
- `SIGN = -1`: this cell reads negative when loaded, and the firmware flips it so a squeeze is positive (verified 2026-11-12).
- `COUNTS_PER_KG = 42952` is a **datasheet estimate, not a calibration** (about ±10 %). `grip_test.CALIBRATION`
  is `"estimated"` until G3 is done, and the app and reports show a banner while it is.
- The HX711 runs at **10 samples/s** (RATE pin low). RFD needs at least 40 Hz and shows n/a until RATE is tied high.
- Opening the serial port restarts the Nano (it re-tares on boot). Only one program can hold the port:
  close the Arduino Serial Monitor before running the app.
- Printed parts are not tested above **34 kg (75 lb)**. Never plan a load above that.

## Rules
- **Honesty about measurements.** Never call forces "calibrated" in code, README, reports or commit messages
  until `software/calibrate.py` has been run on real known-mass data. Say "datasheet-scaled" or "estimated".
- **Git:** work on a branch, open a PR, merge with **"Create a merge commit"** (no squash) so the dated history
  stays. Commit on the day the work happens, and never backdate. Build-log entries carry the real date.
- Run `python -m pytest -q` before every push. Add a test with every behaviour change in the app.
- Keep README claims true: if a feature is untested on the real device, say so.
- When proposing a design or fix, give two or three options and say which one you recommend and why.
