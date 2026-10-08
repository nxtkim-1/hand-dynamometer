# 02 — Printing

## What you print

All files are in `cad/output/print_ready/`. **Every part prints upright, exactly as it's saved — don't rotate anything.**

| Part | File | Colour | ~Mass | ~Cost | Print order |
|---|---|---|---|---|---|
| Fit coupon | `fit_coupon_print.stl` | any | 38 g | $2.70 | **1st** — test your load cell fits |
| Palm half | `palm_half_print.stl` | grey | 86 g | $6.00 | 2nd, after the coupon passes |
| Finger half | `finger_half_print.stl` | black | 78 g | $5.50 | 2nd |
| Cover | `cover_print.stl` | grey | 8 g | $0.60 | any time |
| Calibration cradle | `calibration_cradle_print.stl` | any | ~100 g | ~$7 | before calibration week |

Total about $23. Everything fits the P1S/P2S 256 × 256 mm bed.

## Orientation and supports

- **Palm half** stands on its flat base. The gusset under the internal ledge means **no supports are needed.**
- **Finger half** stands on its bottom rim. It's tall and narrow, so use a **5 mm brim**. Turn on **tree supports** — they'll form only under the dome, which overhangs the seam. Those surfaces face the palm half and are hidden when assembled.
- **Fit coupon** stands on its ring. No supports.
- **Cover** lies flat. No supports.
- **Cradle** lies flat, V-groove up. 3 walls, **15 % infill** — it's a jig, not a structural part.

**Why upright?** The halves are curved shells. Upright, every layer is a complete ring-slice of the shell, which gives the smoothest outside surface and needs the least support. The stresses in the grip are low (a few MPa in a stiff half-tube), so the across-layer direction is well within PETG's strength.

## Where to print — the Rapid Prototyping Centre

The RPC runs Bambu Lab printers. The two you'll use are the **P1S** (18 of them) and **P2S** (12), both with a **256 × 256 mm** bed and able to print PLA, PETG and TPU. Your largest part is 170 × 46 mm, so everything fits with lots of room. The X1C and H2D are for online orders only — you don't need them.

**Cost.** Standard PETG in black, white or grey is **$0.07 per gram**, charged on total mass including supports (you have none). The whole device is about 175 g → **roughly $12–15** including brims and the fit coupon. Teal and transparent PETG are premium at $0.09/g — not worth it.

**Colour tip:** print the palm part in **grey** and the finger part in **black**. It makes the two-part principle visible at a glance in photos and interviews.

**PLA is a fallback, not the plan.** PLA is stronger in tension but brittle — it snaps rather than deforms — while PETG is tougher and bends before it breaks. For a part you squeeze as hard as you can, bending before breaking is the property you want.

## Slicer: Bambu Studio

Because the RPC's printers are Bambu Lab, use **Bambu Studio** (free, bambulab.com → Download). Ignore PrusaSlicer and Cura for this project.

1. Open Bambu Studio → choose printer **Bambu Lab P1S** (or P2S), nozzle **0.4 mm**.
2. Filament: **Bambu PETG Basic** (or "Generic PETG").
3. Process preset: **0.20 mm Standard**.
4. Drag in `cad/output/print_ready/fit_coupon_print.stl`. **Don't rotate it** — it's already lying correctly.
5. Change these from the defaults, in the Strength and Support tabs:

| Setting | Palm and finger halves | Coupon, cover, cradle |
|---|---|---|
| Wall loops | **4** | 3 |
| Top / bottom shell layers | 5 / 5 | 4 / 4 |
| Sparse infill density | **40 %** | 20 % |
| Sparse infill pattern | **Gyroid** | Gyroid |
| Enable support | Off (palm) · **Tree, on** (finger half) | Off |
| Brim | 5 mm on the finger half | none |

6. Click **Slice plate**. The right panel shows estimated grams and time — check it against the table above before you pay for anything.
7. Save the project as a `.3mf` (File → Save project). That file carries your settings, and it's what you bring to the RPC.

**Why PETG:** the parts hold a static load for 30 seconds at a time. PLA creeps (slowly deforms) under sustained load and is brittle; PETG creeps less and bends before it snaps. If the DEN only has PLA, use it with the same settings — it will work, and you'll note it in the report as a limitation.

**Why 5 walls and 40 %:** both parts are loaded in bending along their length. Bending strength lives in the outer skin, which is the perimeters. Infill mostly stops the skins buckling. More walls matter more than more infill.

**Why gyroid:** isotropic — roughly equal strength in every direction, and it doesn't create long straight weak lines the way grid infill does.

## Orientation — do not change it

Both structural parts are long and get bent along their length when you squeeze. The `_print.stl` files lay them **flat on their face**, so the printer builds them up through their thickness. Every layer then runs along the part's length, which means the bending stress stays *inside* layers instead of trying to peel them apart. Printed any other way, a layer line becomes the crack.

The slots come out as horizontal features in this orientation and bridge fine at 0.2 mm. The M6 nut pocket in the finger part has a short bridged ceiling — expect it slightly rough inside, which doesn't matter.

## Getting it printed at the RPC

Bring the `.3mf` project file on a USB stick, or email/upload it — ask the RPC staff which they prefer the first time you go in. They'll confirm the plate type and send it to a P1S or P2S. Bambu printers auto-level the bed, so the classic first-layer problems are much rarer than on older printers, but still watch the first few minutes if you're there.

Bring the `.3mf` or the STL — never G-code. G-code is tied to one printer profile.

## Watching the print

- **Stay for the first layer.** Ninety percent of failures are visible in the first two minutes. If the filament isn't sticking, stop and fix the bed (clean it, re-level, glue stick).
- Check again at ~20 min — the long thin parts are where corners lift.
- After that, leave it. Come back at the estimated time.

## If a print fails

| What you see | Fix |
|---|---|
| Corners lifting off the bed | Clean bed with IPA, add brim, raise bed temp 5 °C |
| Stringing between features | Normal for PETG; trim with a knife |
| Slots too tight for the bolt | Run a drill bit through by hand, or bump `SLOT_W_FIXED` / `SLOT_W_FREE` |
| Nut won't seat in pocket | Bump `NUT_POCKET_AF` +0.2 |
| Layers separating | Print was too cold or too fast — raise nozzle temp 5–10 °C, slow down 20 % |
| Print stopped halfway | Don't try to resume. Reprint. Note it in the build log. |

## Post-processing

Almost none. Remove the brim with a knife. Clear the four slots with a 6.5 mm drill bit run by hand — just to shave stringing, not to enlarge them. Check both ledges are flat; scrape any elephant-foot bulge off with a blade, because a bulged ledge tilts the cell. Sand the outside of both halves lightly if the layer lines feel sharp — these are the surfaces your hand touches.

## Filament budget

Palm ~72 g + finger ~70 g + tray ~4 g + coupon ~27 g = about 175 g, plus margin for one failed print = **plan for 300 g**. Your slicer's estimate is the authoritative number. That's half a standard 1 kg spool. If the DEN charges by weight, this is about $10–15.
