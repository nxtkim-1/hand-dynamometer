# Calibration Report — Hand Dynamometer v1.0

**Authors:** ____________, ____________
**Date of calibration:** ____________
**Device serial / build:** frame print #__, carrier print #__, load cell (supplier, rating) ________

---

## 1. Device description

*One paragraph: what it is, what it measures, what it's for. Labeled photo of the assembled device.*

![Device photo](../images/photo_assembled.jpg)

**Signal chain:** CZL601 100 kg single-point (parallel beam) load cell (130 × 30 × 22 mm, 2.0 mV/V, 405 Ω in / 350 Ω out, class C2) → HX711 24-bit ADC (channel A, gain 128, 10 SPS) → Arduino Nano → USB serial (115200 baud) → `logger.py` → CSV.

Expected sensitivity at 5 V excitation: 10 mV full scale over an HX711 span of ±19.53 mV ⇒ ~43,000 counts/kg. Fitted value below should agree within ±30 %.

**Key dimensions:** grip span 50 mm, grip height 90 mm, frame PETG/PLA (circle one), 5 perimeters, 40 % gyroid.

## 2. Load path

*Explain, with reference to the drawing, why all squeeze force goes through the load cell. State the three clearance checks and that they were performed on the calibration day.*

![Side drawing](../images/drawing_side_dimensions.png)

- Cell body clear of wall: ☐ verified
- Carrier clear of cell below boss: ☐ verified
- Carrier clear of frame: ☐ verified
- Overload stop gap: ____ mm (feeler gauge)

## 3. Calibration method

**Rig:** device rotated 90° and clamped by the head block in a bench vise, palm plate facing down; masses hung from the hook at the bottom of the finger bar via 3 mm cord and a bucket. Direction verified by hand-press and hanging mass giving the same sign. *(Photo.)*

![Calibration rig](../images/photo_calibration_rig.jpg)

**Masses:** source ________; each weighed on ________ (scale make/model or "DEN bench scale"); scale resolution ____ g.

| Nominal | Measured (kg) |
|---|---|
| | |
| | |

**Procedure:** 5 min warm-up; tare with empty bucket; ascending sequence of __ points; descending sequence; 3 complete runs; re-tare between runs.

**Fit model:** `counts = slope × mass + intercept`, ordinary least squares over all __ points (both directions, all runs).

## 4. Results

### 4.1 Calibration curve

![Fit](../images/calibration_fit.png)

### 4.2 Residuals

![Residuals](../images/calibration_residuals.png)

### 4.3 Summary

| Quantity | Value | Method | Cell datasheet |
|---|---|---|---|
| Calibrated range | 0 – ____ kg | max applied mass  0 – 100 kg rated |
| Sensitivity (COUNTS_PER_KG) | ________ counts/kg | fit slope  ~43,000 expected |
| Intercept | ____ counts | fit; should be ≈ 0  zero output ±1.5 % FS |
| R² | 0.______ | fit  — |
| Max nonlinearity | ____ % FS (____ kg) | max |residual| / (slope × 100 kg)  ±0.05 % FS |
| Hysteresis | ____ % FS | max |up − down| at same mass  ±0.05 % FS |
| Repeatability | ____ % FS | max std across 3 runs  ±0.03 % FS |
| Noise floor (1σ) | ____ kg | 60 s unloaded  — |
| Zero drift, 30 min | ____ kg | unloaded  ±0.05 % FS / 10 °C |
| Creep at ~20 kg, 30 min | ____ % of load | loaded  ±0.05 % FS / 3 min |
| **Verification error, unseen mass** | **____ %** (mass ____ kg, read ____ kg) | direct  combined error ±0.05 % FS |

*Full scale (FS) = 100 kg rated. The validated range is the calibrated range above; readings beyond it are extrapolated.*

### 4.4 Interpretation

*Three to five sentences. Compare each measured figure against the datasheet column: anything worse than the cell's own spec came from the frame, the mounting or the reference masses, not the sensor. Where specifically? Does noise matter at all compared with human grip variability of 2–4 kg between consecutive squeezes? Was the ±2 % FS target met?*

## 5. 30-second maximal hold

**Protocol:** seated, elbow 90°, forearm neutral, device held with palm on wall; maximal squeeze sustained 30 s on the word "go"; 2 min rest between hands.

![Hold](../images/hold_plot.png)

| Subject | Hand | Peak (kg) | Time to peak (s) | Force at 30 s (kg) | Decline (%) |
|---|---|---|---|---|---|
| A | L | | | | |
| A | R | | | | |
| B | L | | | | |
| B | R | | | | |

*One paragraph on what the curves show. Compare peaks to published normative data for your age/sex (Mathiowetz 1985) as a sanity check — not as a claim.*

## 6. Limitations

*Write these honestly. Suggested starting list:*

- Calibrated to ____ kg, not full scale; readings above are extrapolated.
- Reference masses verified on a consumer/lab scale of resolution ____ g and unknown calibration status.
- Printed frame in ____ (material) shows creep of ____ % over 30 min under load; readings during long holds include a small frame component.
- Single load cell, single axis; off-axis hand forces are only partially rejected.
- Two subjects, no clinical comparison device.
- Educational device. Not a medical device. Not for diagnosis.

## 7. What we would change

*Two or three concrete things, each tied to something you measured. Examples: thicken the palm plate where you saw deflection; heat-set inserts instead of bolting into printed slots; calibrate to 50 kg with proper weights; compare against a Jamar.*

## Appendix A — Raw data

- `data/calibration_points.csv` (__ rows)
- `data/session_*_cal_run*.csv`
- `data/session_*_noise.csv`, `_drift.csv`, `_creep.csv`
- `data/session_*_hold_*.csv`

## Appendix B — Firmware and software versions

- `grip_firmware.ino` v1.0, `COUNTS_PER_KG = ________`, `SIGN = __`
- Load cell: CZL601-family, ____ kg, supplier ________, nominal 130 × 30 × 22 measured as ____ × ____ × ____
- `calibrate.py`, `analyze_hold.py` — commit ________
