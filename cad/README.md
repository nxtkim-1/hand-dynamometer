# cad/

`dynamometer_cad.py` is the whole mechanical design. Every dimension is a named parameter at the top of the file.

```
pip install cadquery
python dynamometer_cad.py     # all parts -> output/ and output/print_ready/, plus the checks
python render_final.py        # renders -> ../images/
python draw_final.py          # dimensioned drawing -> ../images/final_drawing.png
```

## Parts it makes

| Part | What it is |
|---|---|
| `palm_half` | Grey. Half of the grip plus the base pod. Bolts to the load cell's bottom end. |
| `finger_half` | Black. The other half plus the dome. Bolts to the load cell's top end. |
| `cover` | Closes the base pod. |
| `fit_coupon` | The palm half's clamping zone only. Print first. |
| `calibration_cradle` | V-block that holds the device during calibration. |
| `assembly.step` | Everything in position — open in Fusion 360 or FreeCAD. |

## The checks it runs every time

- Every part is a valid solid.
- Finger half and palm side overlap: **0 mm³** (they never touch).
- Load cell and printed parts overlap: **0 mm³**.
- Load cell's bending zone to both halves: **≥ 3 mm**, measured as a true minimum distance.
- Bolt thread engagement within 1.5× diameter and the cell's thread depth.

## If your load cell is different

Measure it and edit `CT`, `CW`, `CL`, `BOLT`, `SLOT_NEAR`, `SLOT_FAR` at the top. Re-run. The bore, bosses, ledges and slots all follow; the checks tell you if anything no longer fits.

## Drafts for the uncut cable (2026-10-14, not released)

The cable leaves the cell's side 3 mm above its bottom, will not be cut, and needs at least 15 mm of space before it can turn. Two drafts, both reuse the G0-tested clamp, bolt pattern and 3 mm gap:

| Script | What it is | Output |
|---|---|---|
| `compact_base_draft.py` + `render_compact.py` | **v3 compact box** (57 x 82 mm closed base, cable coils inside, 4 M3 cover screws) | `output/draft_compact/`, `../images/compact_v3_*.png` |
| `dish_base_draft.py` | v2 dish (112 x 130 mm open tray, cable coils in view) | `output/draft_dish/`, `../images/dish_draft_v2_*.png` |

`../images/options_compact_vs_dish.png` shows both at the same scale. Everything in those folders is marked DO NOT PRINT until a draft is approved.

## Earlier iterations

`archive/` holds every earlier design — the frame, the two-plate version, the clinical head (A), the symmetric head (S), and the plain split tube. `docs/12_design.md` explains why each was replaced.
