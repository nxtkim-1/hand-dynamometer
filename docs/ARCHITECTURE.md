# Hand Dynamometer: architecture and decision record

The constraint: every gram of force travels through one mechanical load path, and every number on screen traces back to a saved raw sample.

## System walk

A squeeze bends the CZL601 load cell. The HX711 amplifies it, the Nano's firmware (v1.1) prints one CSV line per sample at 115200 baud (`t_ms,raw,net,force_kg`), and the app side, whether the terminal app, the local Flask server, or the browser over Web Serial, runs the same analysis code on those lines. Metrics are computed on a zero-phase filtered copy; the raw samples are saved unchanged under a per-session timestamp, together with the per-trial summary and the centile plot, so any future metric can be computed from existing recordings without re-testing.

## Decision records

### D1. One load path, verified in CAD

- Problem: in a grip dynamometer the reading is only meaningful if the entire squeeze passes through the load cell, with nothing bypassing it through the frame.
- Choice: the handle halves bolt to opposite ends of the cell across a seam (v3 split-grip; v4 Jamar-style two-handle), and the CAD scripts run automated checks on every build: force-path overlap 0.000 mm3, fastener and wire clearance >= 3.2 mm, stress and cable-coil checks ([cad/dynamometer_cad.py](../cad/dynamometer_cad.py), [cad/jamar_v4.py](../cad/jamar_v4.py)).
- Alternative: a dome/flared-base v2 that mounted the cell differently; superseded ([cad/archive](../cad/archive) keeps the history).
- Evidence: the check functions run in the CAD scripts themselves; v4 passes all of them (README CAD status). Onshape part studios regenerate cleanly ([docs/14_cad_open_items.md](14_cad_open_items.md)).
- Not yet measured: VT-09 proof load and VT-10 known-mass calibration are untested; their protocols and pass criteria are fixed in the design and verification report ([docs/report/gripcheck_report.pdf](report/gripcheck_report.pdf), GC-TR-002) before testing, with the bench procedure in [docs/16_vt10_bench_guide.md](16_vt10_bench_guide.md).

### D2. Zero-phase Butterworth for metrics, raw kept raw

- Problem: RFD is a slope, so filter choice can move the number.
- Choice: 4th-order Butterworth low-pass at 10 Hz, applied zero-phase (forward and backward) so peaks do not shift in time; metrics run on the filtered curve while the raw signal is saved untouched.
- Evidence: in a Monte Carlo comparison of 300 simulated trials ([filters.py](../filters.py)), this filter reduced the spread of RFD error with little bias; a 5-point moving average introduced a consistent overestimate.
- Limits: the comparison is on simulated curves, not recorded fault trials.

### D3. Report n/a instead of a bad number

- Problem: the HX711 runs at 10 samples/s until its RATE pin is tied high (80/s), and RFD from a 10 Hz stream is meaningless.
- Choice: the app measures the real sample rate of every recording, adapts the filter to it, and reports RFD as n/a below 40 Hz (MIN_RATE_HZ in [grip_test.py](../grip_test.py)). Forces far above the 100 kg cell rating are treated as "not calibrated yet", not as strength.
- Evidence: hardware-safeguard tests in the pytest suite (34 tests, README) run the full protocol with simulated data and a simulated Arduino speaking the real firmware format.

### D4. Calibration is device state, not code

- Problem: a counts-per-kg constant edited into source silently changes every past and future reading.
- Choice: the scale factor and sign live in the Nano's EEPROM, set from the Calibrate web page with known masses (serial commands C/S/R/I; firmware v1.1). Until then the firmware starts from the datasheet estimate (42,952 counts/kg, about +/-10%) and announces `# calibration=estimated`; the app and every report carry the same banner. The sign differs per frame (v3: -1, verified 2026-11-12; v4.2: +1, reported 2026-11-23) and is fixable on the device without re-uploading. The measured procedure is documented in [docs/04_calibration.md](04_calibration.md).
- Alternative considered and rejected in practice: baking a measured value into the Python `CALIBRATION` flag, which is separate and still set by hand (documented as such).
- Not yet measured: the measured calibration itself; see D1.

### D5. One analysis core, three front doors

- Problem: terminal app, local web app and public demo drift apart if each re-implements the protocol.
- Choice: [webapp.py](../webapp.py) reuses [grip_test.py](../grip_test.py)'s protocol, metrics, filtering, quality check, saving and report; only interaction changes (its own module docstring states this). The live graph is Server-Sent Events; Web Serial uploads land on the same analysis path. The demo mode (`GRIPCHECK_DEMO=1`, also forced on stateless hosts) simulates every squeeze, keeps each visitor's session separate, and disables the "newest report" page so strangers' results are never shown.
- Evidence: the pytest suite runs the protocol end to end in both the terminal and web apps.
- Limits: all pipeline results so far are on simulated signals; agreement with a clinical Jamar device (Bland-Altman plan in the README) is future work.

## Interview questions this doc should let the owner answer

- Why does RFD become n/a at 10 Hz, and what in the code enforces it?
- Two visitors open the demo at once; what keeps their trials apart?
- A calibration saved on v3 moves to a v4.2 frame; what breaks and where is it fixed?
