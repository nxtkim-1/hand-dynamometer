# 02 — Printing

## What you print (v3)

All files are in `cad/output/print_ready/`, numbered in print order. **Every part prints exactly as it's saved — don't rotate anything, keep scale at 100 %.**

| File | Colour | How it sits | Supports | ~Mass / note | Print order |
|---|---|---|---|---|---|
| `1_base_test_v3.stl` | any | Open bottom on the bed | **Tree, "on build plate only"** (forms only under the box ceiling) | ~52 g before supports; box + clamp zone only — tests the cable, coil, boards and USB fit on the real cell | **1st** — skip if it already passed |
| `2_palm_half_v3.stl` | grey | Open bottom on the bed, half-grip pointing up | **Tree, "on build plate only"** | ~182 mm tall, 57 × 82 mm footprint | 2nd |
| `3_finger_half_v3.stl` | black | **Upside down, on its flat top** (as the file loads — don't flip it) | **Off**, no brim | ~137 mm tall, round footprint | 2nd |
| `4_cover_v3.stl` | grey | Flat, rail facing up | Off | 14 mm tall | any time |

Cost: about **$17–24** for all four. Everything fits the P1S/P2S 256 × 256 mm bed. The fit coupon already passed G0 and the v1/v2 files are in `cad/archive/superseded_2026-10-16/`.

**Not printable yet: the calibration cradle.** It was designed for the old round base and needs a redesign for the v3 box base. Not needed until calibration (G3).

**Colour tip:** palm half in **grey**, finger half in **black** — it makes the two-part principle visible at a glance in photos and interviews.

## Settings (Bambu Studio, PETG, any P1S or P2S)

Because the RPC's printers are Bambu Lab, use **Bambu Studio** (free, bambulab.com → Download).

1. Printer **Bambu Lab P1S** (or P2S), nozzle 0.4 mm; filament **Bambu PETG Basic** (or Generic PETG).
2. Drag in the STL. **Don't rotate it** — each file is already oriented.

| Setting | Value |
|---|---|
| Process | **0.12 mm Fine** (or 0.16 mm Optimal if short on time) |
| Wall loops | **4** |
| Sparse infill | **25–40 %, gyroid** |
| Seam position | **Aligned**, on the side seam between the halves |
| Outer wall speed | ~60 mm/s |
| X-Y hole compensation | **0** |
| Scale / rotation | 100 %, no rotation |

3. Slice and check the estimated grams and time against the table before paying. Files 2 and 3 are the long prints at 0.12 mm — start those first if the RPC has two printers free.
4. Save the project as a `.3mf` — that carries your settings and is what you bring to the RPC.

**Why PETG:** the parts hold a static load for 30 seconds at a time. PLA creeps under sustained load and is brittle; PETG creeps less and bends before it snaps. PLA is a fallback, not the plan — same settings, note it as a limitation.

**Why 4 walls and gyroid:** the parts are loaded in bending along their length; bending strength lives in the outer skin (the perimeters), and infill stops the skins buckling. Gyroid is roughly equal in every direction and leaves no long straight weak lines.

**Supports on files 1 and 2** stand on the bed inside the open box, so you pull them out through the bottom after printing.

Expect roughly 1.5–2× the time of the RPC's quick 0.20 mm preset. Finish the grip afterwards with 220 then 400 grit sandpaper.

## At pickup

- Run a **7 mm drill bit by hand** through the six bolt holes to clear stringing.
- Peel out the supports.
- Once assembled, check that **paper slides in the 3 mm gaps** all the way round.

**Bring with you:** 6 × M6 × 25 with washers, 4 × M3 × 10, and the 4 mm hex key.

## Getting it printed at the RPC

Bring the `.3mf` project file on a USB stick, or email/upload it — ask the RPC staff which they prefer the first time you go in. They'll confirm the plate type and send it to a P1S or P2S. Bambu printers auto-level the bed, so first-layer problems are rare, but watch the first few minutes if you're there.

Bring the `.3mf` or the STL — never G-code. G-code is tied to one printer profile.

## Watching the print

- **Stay for the first layer.** Ninety percent of failures are visible in the first two minutes. If the filament isn't sticking, stop and fix the bed (clean it, re-level, glue stick).
- Check again at ~20 min — the long thin parts are where corners lift.
- After that, leave it. Come back at the estimated time.

## If a print fails

| What you see | Fix |
|---|---|
| Corners lifting off the bed | Clean bed with IPA, raise bed temp 5 °C |
| Stringing between features | Normal for PETG; trim with a knife |
| Slots too tight for the bolt | Run a drill bit through by hand |
| Layers separating | Print was too cold or too fast — raise nozzle temp 5–10 °C, slow down 20 % |
| Print stopped halfway | Don't try to resume. Reprint. Note it in the build log. |

## Filament budget

Roughly 300–350 g including supports and margin for one failed print — under half a 1 kg spool. The slicer's estimate is the authoritative number.
