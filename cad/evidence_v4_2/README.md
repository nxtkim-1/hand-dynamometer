# Engineering evidence pack: v4.2 (as printed)

The design is frozen: these files only **read** `../jamar_v4_2_review/`. Every claim is tagged:
**[GEOMETRIC-ONLY]** from the exported CAD, **[SIMULATED]** from synthetic data, **[PHYSICAL]** from the real
device. Nothing is [PHYSICAL] yet: the parts are printed but not assembled, proof-loaded or calibrated.

| File | What it is |
|---|---|
| `check_v4_2.py` | Reproducible geometry checks; writes `check_v4_2_report.json` and `inspection_sheet.csv` |
| `check_v4_2_report.json` | Last run: **53 / 53 checks pass** [GEOMETRIC-ONLY] (2026-11-22) |
| `inspection_sheet.csv` | Features to measure on the printed parts, with nominal values from the source and accept ranges |
| `slicer_profile_draft.md` | Record of the print settings actually used (fill in) + a draft profile for reprints |
| `../../docs/15_calibration_v4_2.md` | Proof-load and calibration protocol for this frame |
| `../baseline_reconciliation/` | Why v4.2 is the baseline, and the annotated holding view |

## What `check_v4_2.py` checks [GEOMETRIC-ONLY]

- Each of the 5 parts is one valid STEP solid; each print STL is watertight with consistent winding; STEP and
  STL volumes agree within 1 %; each part lies flat and fits a 240 × 240 mm bed (Z limit assumed 250 mm).
- All 6 combined plates fit 240 × 240 mm.
- No printed part overlaps another in the assembly (10 pairs, 0.0000 mm³).
- The finger part can move 17.1 mm toward the palm before touching anything fixed (no force bypass on the
  squeeze axis).
- The source rebuilds the exported palm bar exactly (0.000 % volume difference), so it is editable.
- At **all 5 palm settings** the palm bar overlaps nothing, and moves only 0.35 mm before bearing on the frame's
  keyed seat (the M5 bolts are not the load path in the geometry).

Run it (CadQuery environment):

```
python check_v4_2.py                  # default bed 240 x 240 x 250 mm
python check_v4_2.py --bed 256 256 256
```

## Open risks (none resolved physically)

1. Keyed palm seat: exists in the geometry; PETG bearing/lug strength untested.
2. Cable: real length unknown (v4.2 assumes ~8 cm, repo docs say ~1 m). v4.2's own validation fails its cable
   bend check (R 1.9 mm modelled). Measure the cable before closing the pod.
3. Coil/bay capacity verified geometrically only; Dupont housing and HX711 sizes are assumptions.
4. M3 self-tap pilots (2.75 mm) are untested in PETG, although the v4.2 source calls them "proven".
5. No fit coupons printed (the parts were printed directly): use `inspection_sheet.csv` instead.
6. Hand fit: about 88 mm four-finger window, 21.5 mm fingertip pocket; no measured hand yet.
7. No FEA was done. No physical strength, creep or calibration test yet.
