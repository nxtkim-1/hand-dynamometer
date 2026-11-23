# 15 - Proof load and calibration of the v4.2 (Jamar-style) device

Status 2026-11-22: v4.2 parts are printed. **Not yet assembled, proof-loaded or calibrated.** The firmware
still uses the datasheet estimate of 42,952 counts/kg (about ±10 %). This page is the plan; nothing in it has
been done yet. `docs/04_calibration.md` covers the old v3 barrel and does not apply to this frame.

Hard limit: **34 kg (75 lb) total including the hanger and strap.** The printed parts are untested above that.

## 1. The principle, for this frame

A squeeze pushes the palm onto the palm bar and pulls the **finger bar's back face toward the palm** (the -x
direction in the CAD; see `cad/baseline_reconciliation/holding_view_v4_2_annotated.png`). That force goes
finger bar → finger part → 3 × M6 → load cell → 3 × M6 → frame → keyed seat → palm bar.

Calibration masses must load the cell **the same way**: pull the finger bar's back face toward the palm bar,
with the frame held still. Hanging weight from anywhere else (the load cell, the frame, the bracket above the
fingers) gives readings that look fine and are wrong.

## 2. Rig (to be built and checked; not designed as a printed part)

1. Turn the device so the **palm bar points down** and the finger bar is above it: the squeeze direction now
   points straight down, the same way as gravity.
2. Support the **frame** on two wooden blocks under its top and bottom arms, so the palm bar and finger bar hang
   free between them. **Do not clamp the printed frame in a vise.**
3. Loop a flat strap (webbing, about 25 mm wide) over the finger bar's back face at **middle-finger height**.
   Run both legs down the open sides of the bars (outside the palm bar, touching nothing), and join them under
   the device to the hanger.
4. The strap may touch only the finger bar. If it touches the palm bar, frame, pod or guard, the force bypasses the
   cell: re-route it.
5. **Direction check, do not skip.** Squeeze the bars by hand: `net` goes positive. Hang a small mass on the
   strap: `net` must also go positive. Different signs mean the device is upside down in the rig.

## 3. Before any mass: printed-part inspection

Fill in `cad/evidence_v4_2/inspection_sheet.csv` with calipers. Then check:
- the finger part moves freely, with paper sliding through every gap to the frame (no rubbing anywhere);
- no cracks or white stress marks at the M6 counterbores or the keyed palm pockets;
- the palm bar sits fully in its keyed seat at setting 2 and the M5 bolts are snug, not crushing the plastic.

## 4. Proof load (first contact with real force)

Goal: show the printed structure holds and returns to zero **before** anyone squeezes it hard.

Start the logger once and keep it running for the whole sequence (opening the port reboots the Nano and
re-zeroes it):

```
python software/logger.py COM7 --label proof_v42
```

| Step | Load (incl. hanger) | Hold | Then check |
|---|---|---|---|
| 1 | 5 kg (11 lb) | 30 s | unload; `net` back within ±200 counts of zero; look at the bosses |
| 2 | 10 kg (22 lb) | 30 s | same |
| 3 | 15 kg (33 lb) | 30 s | same |
| 4 | 20 kg (44 lb) | 30 s | same |
| 5 | 30 kg (66 lb) | **5 min** | creep: note `net` at 10 s and 5 min; unload; zero return |

Stop at the first crack, creak, visible bending of the arms, or a zero that does not come back. Write down
what happened; do not continue with a damaged part.

## 5. Calibration runs

Use the plate plan in `docs/HANDOFF.md` (0 → 72.5 lb in 10 steps, up then down, three runs; skip the top
step if the hanger pushes the total over 75 lb). Weigh every plate and the hanger first, and use the
**weighed** values. Fill `data/calibration_points.csv` (copy `data/calibration_points_template_lb.csv`).

Each step: lower the old load gently, hang the new one, wait 10 s, read the stable `net` (the logger prints the
mean of the last 2 s on exit; while running, note the value by eye).

Then fit:

```
python software/calibrate.py data/calibration_points.csv            # --source measured is the default
```

It prints COUNTS_PER_KG, intercept, R², nonlinearity, hysteresis, repeatability, the calibrated range, and a
**curvature check** (whether a straight line is good enough), and saves two plots.

## 6. Two extra checks this frame needs

- **Strap position (eccentric load).** Hang one middle load (about 25 lb) with the strap at little-, middle- and
  index-finger height in turn. A parallel-beam cell should read nearly the same. Report the spread as
  % of the reading; a large spread means the reading depends on where the hand squeezes.
- **Zero stability.** 60 s at rest with nothing loaded, before and after the session. `software/pipeline.py`
  `rest_stats()` gives noise and drift.

## 7. After the session

1. Paste COUNTS_PER_KG into `firmware/grip_firmware_tillaart/grip_firmware_tillaart.ino`, and change its
   `# calibration=` line to `measured`. Re-upload.
2. Set `CALIBRATION = "measured"` in `grip_test.py` (Samuel's file: via a PR he reviews) and in
   `website/src/lib/protocol.ts`.
3. Old recordings made with the datasheet factor can be re-scaled with `pipeline.apply_calibration()`.
4. Update the README calibration status with the real numbers and the calibrated range only (for example
   "0–33 kg"), plus a dated build-log entry with the plots.

Only after all of this may forces be called calibrated, and only within the calibrated range.

## 8. What the tests already show, and what they do not

`software/tests/test_pipeline.py` runs this whole procedure on a **simulated** cell
(`software/synthetic_cell.py`) whose true counts per kg, hysteresis and noise are known, and checks that the
fit recovers them. That proves the arithmetic. It says nothing about this device's real accuracy.
