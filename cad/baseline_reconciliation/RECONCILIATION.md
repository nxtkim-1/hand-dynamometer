# Jamar v4.1 vs v4.2: which CAD is the working baseline? (2026-11-22)

Every claim below is tagged. **[GEOMETRIC-ONLY]** = measured from exported STEP/STL files. **[DOC]** = taken from a
package's own notes and not independently checked. No part has been printed, assembled, load-tested or
calibrated, so nothing here is **[PHYSICAL]**.

## 1. What the packages contain

| Package | What it really is |
|---|---|
| `jamarv4_1cadhandoffandt3continuationpromptuntested.zip` | Inner zip `Jamar_v4_1_CAD_handoff_T3_20261120.zip` + prompt + preview PNG |
| `latestjamarv4_1cadfullt3promptholdingviewclarifi.zip` | **The same inner zip** (identical SHA-256, `5d95c67de820dabd…`) + a prompt that adds only the "show a holding view first" request |
| `Jamar_v4_2_FINAL_print_files.zip` | 27 files: 5 STEP parts + assembly + hardware envelopes, print STLs, 240 × 240 plates, renders, README, validation JSON. **No source code.** |
| `cad/jamar_v4_2_review/` (repo, untracked) | The v4.2 zip **plus its source** (`jamar_v4_2_review.py`, `build_and_render_v4_2.py`, `make_combined_plates.py`) and three fit-coupon STEP/STLs. All 27 zip files are byte-identical to the folder copies. |
| `cad/jamar_v4_1_holding_review/` (repo, untracked) | Two images only: an annotated holding view of v4.1 and its raw render |

So there are two candidates, v4.1 and v4.2. The v4.1 handoff includes its source (`src/`) and the original v4
baseline. v4.2's source lives only in the repo folder, and it imports `cad/dynamometer_cad.py` (measured
load-cell constants), so it rebuilds only inside this repo. Both use the measured 130 × 40 × 22 mm cell.

## 2. Geometry check of all exported parts [GEOMETRIC-ONLY]

`python compare_parts_v41_v42.py <v4.1 dir> <v4.2 dir>` (CadQuery + trimesh):

| Part | v4.1 STEP | v4.2 STEP | Print STL (both) |
|---|---|---|---|
| frame | 1 valid solid, 334.8 cm³, 195 × 36 × 231 mm | 1 valid solid, 327.6 cm³, 180.5 × 36 × 214 mm | watertight, winding OK |
| palm bar | 70.8 cm³, 105.6 mm long | 89.1 cm³, 141.8 mm long (keyed lugs) | watertight, winding OK |
| finger part | 98.0 cm³ | 93.9 cm³ | watertight, winding OK |
| pod cover | 118.2 cm³, 231 mm | 113.7 cm³, 214 mm | watertight, winding OK |
| guard | 52.2 cm³, 231 mm | 48.0 cm³, 214 mm | watertight, winding OK |

STEP and STL volumes agree within 0.9 %. v4.2's housing is 17 mm shorter because v4.1's deep coil bay was removed.

## 3. The differences that matter

| Question | v4.1 | v4.2 |
|---|---|---|
| Can the hand hold it the right way? | **No.** Its own exact-section holding view shows the convex palm pad and finger scallops facing the empty gap, and the upper bracket blocking index and middle fingers [GEOMETRIC-ONLY, `cad/jamar_v4_1_holding_review/`] | **Yes, geometrically.** Contours face the squeeze; four-finger window z 3.5 to about 92 mm, about 88 mm tall [GEOMETRIC-ONLY, measured] |
| Palm-bar load path | Only two M5 bolts in shear, no shoulder [DOC] | **Keyed seat exists:** the palm bar moves 0.35 mm in +x, then bears on frame PETG [GEOMETRIC-ONLY, `measure_grip_v42.py`]. PETG strength untested |
| Force bypass on squeeze axis | 0 overlap, ≥ 3.2 mm air [DOC] | Finger part moves 17.1 mm toward the palm before touching anything [GEOMETRIC-ONLY]. Other axes not re-measured here |
| Grip span, setting 2 | 82 mm palm-to-finger reach [DOC, from its holding view] | 54.0–54.5 mm measured at y = 0, z = 40–90 [GEOMETRIC-ONLY]; v4.2 notes say 56.0 |
| Cable storage | Coil bay sized for about 1,079 mm, tight R ≈ 8 mm turns [DOC] | Built for a "user-reported ~8 cm" cable. **Its own validation fails** `routed_8cm_cable_zero_interference_and_gentle_bend` (routed 57.5 mm, tightest bend R 1.9 mm, impossible for a 5.13 mm jacketed cable) [DOC, read from `validation_v4_2.json`] |
| Fit coupons | None | Three coupon STEP/STLs in the repo folder, but not in the zip; README wrongly says coupons are not needed |

## 4. Recommendation

**Use v4.2 as the working baseline for the grip, frame and palm seat. Keep it blocked on the cable until the real
length is measured.**

- v4.1 cannot be held correctly, so its grip is disqualified regardless of anything else.
- v4.2 fixes the grip direction and replaces bolt-shear palm loading with a keyed shoulder (in geometry).
- But v4.2's electronics bay assumes an ~8 cm cable. `docs/12_design.md` says about 1 m of spare cable, and the
  build log says it was never measured. If it is about 1 m, v4.2 has nowhere to put it.

Options once the cable is measured:

1. **Cable ≤ ~10 cm:** keep v4.2 as is, but fix the cable route so its bend radius is realistic (fails today).
2. **Cable much longer (recommended assumption until measured):** port a v4.1-style coil bay into the v4.2 frame,
   with a larger bend radius than v4.1's R ≈ 8 mm.
3. **Cut and re-terminate the cable:** smallest bay, but it breaks the project's "do not cut the cable" rule and
   needs re-soldering. Not recommended.

## 5. Open risks carried forward (none resolved physically)

1. Palm load path: keyed seat now exists [GEOMETRIC-ONLY]; PETG bearing and lug strength untested.
2. Cable: real length unknown; v4.2 route fails its own bend check; v4.1 coil bends are tight.
3. Coil/bay capacity checked geometrically only; connector and HX711 dimensions assumed.
4. Hand fit: about 88 mm four-finger window and 21.5 mm fingertip pocket; no measured hand yet.
5. No fit coupon printed, no slicer profile checked, no physical strength or calibration test.

## 6. Annotated holding view

`holding_view_v4_2_annotated.png`, made by `holding_view_v4_2.py` from the v4.2 assembly STEP. Solid fills are exact
B-rep sections; the hand is illustrative only.

Before any grip change, please give:
- hand breadth across the four knuckles (mm), and
- the real cable length from the cell to the bare wire ends (mm).

## Reproduce

Run with the WSL CadQuery environment (needs cadquery, shapely, matplotlib; trimesh for the first script):

```bash
python compare_parts_v41_v42.py <unzipped v4.1 jamar_v4_1_review> <unzipped v4.2 print files>
python measure_grip_v42.py ../jamar_v4_2_review/output/jamar_v4_2_review_assembly.step
python holding_view_v4_2.py ../jamar_v4_2_review/output/jamar_v4_2_review_assembly.step holding_view_v4_2_annotated.png
```
