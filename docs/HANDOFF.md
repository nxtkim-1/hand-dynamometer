# Handoff: where the project stands (2026-11-12)

Written when work moved from the Claude app to Claude Code on Thomas's laptop. Update the status table and
tick tasks off as they are done; this file is loaded into every Claude Code session through `CLAUDE.md`.

## Status

| Gate / item | State | Evidence |
|---|---|---|
| G0 printed parts fit the cell | Passed | build log 2026-10 |
| G1 first signal on the bench | **Passed 2026-11-06** | rest about +52,400 counts, noise about ±70; press went negative → SIGN = -1 |
| G2 assembled grip reads and returns to zero | **Passed 2026-11-12** | squeeze reads positive with SIGN = -1. Peak `net` and after-release values **not yet logged** |
| G3 calibration with known masses | **Not done** | firmware uses the datasheet estimate 42952 counts/kg |
| G4 closed-book quiz (load path, seam rule, calibration) | Not done | |
| PR #3 hardware docs + Tillaart firmware | Merged | |
| PR #4 GripCheck reads the real device (Web Serial, `--device`, calibration banner) | **Open, waiting for Samuel** | 50 tests pass; browser flow checked with a simulated device only |
| Real Nano + GripCheck end to end | Not done | |
| HX711 at 80 Hz (RATE pin) | Not done | needs a photo of the board |

## To do, in order

### 1. Merge PR #4 (Samuel)
Samuel reviews github.com/nxtkim-1/hand-dynamometer/pull/4 and merges with **Create a merge commit**.
Then pull `main` (GitHub Desktop: Fetch origin → Pull).

### 2. First real test with GripCheck
1. Upload `firmware/grip_firmware_tillaart/grip_firmware_tillaart.ino` again (it now prints a calibration comment line).
2. Close the Arduino Serial Monitor.
3. Run **either** `python webapp.py --device` **or** `python webapp.py`, then press **Connect device** in Chrome or Edge.
4. Do the whole test: zero, 6 squeezes, 30 s hold, then the report.
5. Expected: "Device connected" badge, the estimated-calibration banner, about 10 samples/s, RFD n/a.
6. Save the report as PDF and add a screenshot to `docs/proofs/`. Write a dated build-log entry with peak values.
Done when: a real report exists and is logged. Also add the missing G2 numbers.

### 3. Live demo on Render
- Merging to `main` redeploys if auto-deploy is on (the default for `render.yaml` Blueprints). Otherwise, in Render:
  **Manual Deploy → Deploy latest commit**.
- Open the live link in Chrome, press **Connect device**, and run one trial with the real device.
- Put the live link in the README.

### 4. G3 calibration (one session, about 2 h, two people is easier)
- Procedure: `docs/04_calibration.md`. Load the cell exactly the way a squeeze does, and do the direction check first.
- Fixture: options are two 2×4s screwed into a V (fastest), or a printed V-cradle for the 57 × 82 mm v3 box
  (not designed yet). Do not clamp the printed box in a vise.
- Weigh every plate and the hanger first. Hard limit **75 lb total including the hanger**.
- Plate plan (one of each plate: 2.5, 5, 10, 25, 30, 35, 40, 45, 50 lb). Each step is a swap: lower the old load
  gently, hang the new combination, wait 10 s, then read `net`. **Never restart the logger mid-run**, because that re-zeroes with weight on.

  | Step | lb | Plates |
  |---|---|---|
  | 0 | 0 | empty hanger |
  | 1 | 5 | 5 |
  | 2 | 10 | 10 |
  | 3 | 17.5 | 10 + 5 + 2.5 |
  | 4 | 25 | 25 |
  | 5 | 35 | 35 |
  | 6 | 45 | 45 |
  | 7 | 55 | 50 + 5 |
  | 8 | 65 | 50 + 10 + 5 |
  | 9 | 72.5 | 45 + 25 + 2.5 (skip if the hanger pushes the total over 75 lb) |

  Up 0→9, down 8→0, three runs.
- Fill `data/calibration_points_template_lb.csv` (copy it to `data/calibration_points.csv`). Replace `mass_lb`
  with the **weighed** values and type the stable `net` into `net_counts`.
- `python software/calibrate.py data/calibration_points.csv` gives COUNTS_PER_KG, R², nonlinearity, hysteresis
  and repeatability, plus two plots.
- Then: paste COUNTS_PER_KG into the firmware and change its `# calibration=` line to `measured`. Set
  `CALIBRATION = "measured"` in `grip_test.py` (a PR, since that is Samuel's file). Update the README
  calibration status with the real numbers and the calibrated range. Write a build-log entry with the plots.
- Quick check first if wanted: hang only the 25 lb plate. Expected `net` is about 11.34 × 42952 ≈ 487,000 counts.

### 5. HX711 to 80 samples/s (optional, enables RFD)
On most HX711 boards the chip's RATE pin is tied to GND by a trace; tying it to VCC gives 80 Hz. Board layouts
differ, so **take close-up photos of both sides of the board first** and identify the RATE trace or jumper before
cutting anything. Afterwards GripCheck should report about 80 samples/s and show RFD values. Re-run G2 after this
change. Re-run G3 too if it was done at 10 Hz, since the noise is higher at 80 Hz.

### 6. G4 quiz, then the resume bullet
Closed-book: the load path, the seam rule, and how calibration turns counts into kg. After G3, update the resume
bullet with the measured numbers (COUNTS_PER_KG, nonlinearity %, repeatability %, calibrated range). Until then,
describe it as "datasheet-scaled, calibration in progress".

## Known details
- This repo on GitHub is the source of truth. An older local copy used during the Claude-app sessions has a
  different commit history and should not be pushed.
- Sample lines from the device: `1234,52410,0,0.000` (t_ms, raw, net, force_kg).
- Bench numbers: rest about +52,400 raw counts, noise about ±70 counts (about 2 g at 43,000 counts/kg).
