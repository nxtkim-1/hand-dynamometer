# Slicer profile: v4.2 (DRAFT, and a record of what was actually used)

The v4.2 parts are already printed. This page has two jobs:

1. **Record** the settings that were really used, so a reprint or a failure can be traced. Fill in the right-hand column.
2. **Suggest** a starting profile for any reprint. These suggestions are not verified by a print or a strength test.

Nothing here changes the design. Orientation is fixed by the exported STLs: drop them on the bed **without rotating**.

| Setting | Draft suggestion | Why | **Actually used** |
|---|---|---|---|
| Printer / bed | 240 × 240 mm (from the plate files) | combined plates are laid out for this bed | |
| Material | PETG | tougher and less brittle than PLA under repeated load; better creep resistance at room temperature | |
| Nozzle | 0.4 mm | standard; teardrop holes assume normal bridging | |
| Layer height | 0.20 mm | balance of strength and time | |
| Walls (perimeters) | 5 (≥ 2.0 mm) | load goes through bolt bosses and the keyed seat walls: perimeters carry it, not infill | |
| Top / bottom layers | 6 / 6 | solid skin around counterbore floors and the keyed pockets | |
| Infill | 40 % gyroid | gyroid is roughly isotropic; 40 % backs the walls without much extra weight | |
| Supports | none | the exported parts are designed support-free (teardrop holes, flat bottoms) | |
| Brim | 5 mm on the frame only, if it lifts | tall thin frame edges can warp on PETG | |
| Nozzle / bed temperature | follow the filament maker (typical PETG 235–245 °C / 75–85 °C) | | |
| Cooling | 30–50 % | PETG layer bonding drops with heavy cooling | |
| Seam | rear / aligned, away from the hand faces | keeps seams off the palm and finger surfaces | |
| Plate option used | A, B or C (see `../jamar_v4_2_review/README_v4_2_review.md`) | | |
| Filament brand / colour | | | |
| Print date, time per plate | | | |

## Things to inspect on the printed parts before assembly

Use `inspection_sheet.csv` in this folder (calipers, plus a sheet of paper for the air gaps). Also look for:

- layer separation or white stress marks around the M6 counterbores and the keyed palm pockets;
- the 1.61 mm webs between paired M6 counterbores: present and not cracked;
- warped frame edges (lay it on a flat table: no rocking).

Any crack, delamination or rocking means **stop**: do not load the part.

## Not established

Print strength, layer adhesion, creep under a sustained hold, and the safe load of the printed frame are all
untested. A slicer profile is not a strength rating. Loads stay at or below 34 kg (75 lb) including the hanger
until a proof-load plan has been carried out (`docs/15_calibration_v4_2.md`).
