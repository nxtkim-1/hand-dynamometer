# 01 — Design process

> **The final design is described in `12_design.md`.** This document records the original requirements and early concept thinking; its architecture sections describe superseded versions.

This document records how the design was arrived at, so that someone reading the repo (or interviewing you) can see the reasoning and not just the result.

## 1. Requirements

Written before any geometry. Every line has a number so it can be tested.

| ID | Requirement | Test |
|---|---|---|
| R1 | Measure grip force 0–100 kgf | Load cell rating; calibration to ≥ 30 kg |
| R2 | Accuracy within ±2 % of full scale after calibration | Verification against an unseen reference mass |
| R3 | All squeeze force passes through the load cell — no parallel load path | Inspection: nothing touches the cell or carrier except through the bolts |
| R4 | Grip span (palm face to grip face) 50 mm | Measure the printed part |
| R5 | Sampling ≥ 10 Hz | Timestamp interval in the CSV |
| R6 | Calibration must load the cell in the same direction and through the same path as a squeeze | Procedure design (hang masses from the grip) |
| R7 | No electrical path to the user | Continuity test grip → electronics |
| R8 | Mechanical stop before cell overload | Stop bolt, 0.5 mm gap, verified with a feeler gauge |
| R9 | Every non-electronic part 3D-printable on a 220 × 220 mm bed with no supports | Slicer check |
| R10 | Printed parts survive 60 kgf without yielding (PETG or PLA) | Hand calculation, below; then a 30 s hold at max effort
| R12 | Mount accommodates cell hole spacing anywhere from 8 to 50 mm from each end face | Fit coupon test before the frame is printed |
| R13 | Every part printable on a 220 x 220 mm bed | Slicer check: largest is 170 x 46 mm |
| R14 | Handheld; no bench, stand or base required | Hold it and squeeze |
| R11 | Fully reproducible from the repo: STLs, firmware, BOM, procedure | A third person can build it from the README alone |

R3 and R6 are the two that decide whether the numbers mean anything. Everything else is secondary.

## 2. Three concepts

The problem is: get hand-squeeze force into a load cell along its intended axis, repeatably, with the hand in a standard position.

### Concept A — Cantilever post (chosen)

A bar-type load cell stands vertically. Bottom bolted to the palm wall; top carries the moving grip. Fingers pull the grip toward the palm and bend the cell.

- Parts in the load path: zero besides the cell and four bolts
- Friction or pivots: none
- Printed parts: 2 structural (frame, carrier) + tray
- Weakness: printed carrier and wall are cantilevers, so they need enough section to not flex or yield

### Concept B — Hinged lever

Moving handle pivots on a hinge at the bottom. A button-type compression load cell sits between the handle and frame near the hinge. Mechanical advantage means the cell sees more force than the hand applies, which improves resolution.

- Rigid feel, compact
- Weakness: the pivot is a friction and clearance source — every dynamometer that uses one shows hysteresis from it. Needs a different (button) cell. Lever ratio must be calibrated in and any pivot wear changes it. More parts.

### Concept C — Parallel plates on guide pins

Two grip plates squeeze a compression cell between them, kept aligned by two guide pins.

- Pure axial loading of the cell
- Weakness: guide pins bind and rub under any off-axis hand force — this is the classic way to get 5 % hysteresis. Printed pins and bores make it worse.

### Decision

| Criterion | Weight | A: Post | B: Lever | C: Plates |
|---|---|---|---|---|
| Purity of load path (R3) | 5 | best | pivot | pins |
| Hysteresis risk | 5 | lowest | medium | highest |
| Parts count / printability (R9) | 3 | 3 parts | 6+ | 5 |
| Uses the cheap bar cell that ships with an HX711 | 2 | yes | no | no |
| Rigidity of feel | 2 | good | best | good |

A wins on the two heavily-weighted rows. It loses slightly on feel, which a stiff wall and gusset recover. B is what you'd build if you needed higher resolution from a small cell — not the case here, since the cell resolves ~5 g against grip variation of kilograms.

## 3. Why the parts are shaped the way they are

**The wall is thick with a gusset behind it.** Your palm applies up to ~600 N to the wall at about mid-height. For a cantilever 18 mm thick and 45 mm wide, bending stress at the root would be about 600 N × 0.10 m / (0.045 × 0.018² / 6) ≈ 25 MPa — too close to PLA's practical limit, and it would visibly flex. The triangular gusset up to z = 150 makes the effective section at the root ~60 mm deep, dropping root stress to a few MPa. Above the gusset the unsupported height is only 40 mm, so that stress is small too.

**The frame is printed lying on its side.** The whole frame is a 2D profile extruded 45 mm. Printing it on that flat profile face puts every layer *parallel* to the bending plane. Bending loads then run *along* layers instead of trying to peel them apart. This is the single most important printing decision in the project, and it's why there's no fixed handle "rod" — a tall printed cylinder would have to be printed vertically and would snap at a layer line. A wall is stronger, prints flat, and is actually closer to what clinical dynamometers do (the Jamar body sits against the palm).

**Two parts on opposite faces of the cell.** The palm part bolts to the cell's lower end and rises on the palm side; the finger part bolts to the upper end and hangs on the finger side. They interleave without ever touching — 2 mm of air everywhere. Squeeze and the only thing joining them is the cell, so the cell reads the whole force.

This replaced an earlier version with a base plate, a palm wall and a triangular gusset that sat on a table. That version worked but was wrong in a way worth recording: it was a bracket, not an instrument. It weighed twice as much, took 15 hours to print, needed four different fastener sizes, and had a calibration tab bolted on the top like a wart. Asking "what does a real dynamometer look like?" produced this instead — handheld, 74 × 46 × 170 mm, two printed parts, five identical bolts, under 9 hours of printing.

**The base plate went away entirely.** It existed only so the device could be clamped during calibration. Clamping the head block instead does the same job with no extra material.

**Loading the cell along its length is fine — that is what a single-point cell is for.** The CZL601 is rated for a 250 × 250 mm platform, meaning ±125 mm of eccentricity. The palm and finger loads are spread over ~90 mm of the cell's length, well inside that. A plain beam cell without eccentric-load compensation could not be used this way.

**The finger bar hangs 18 mm below the palm plate for one reason.** During calibration the cord must hang straight down without touching anything. Putting the hook below where the palm plate starts is the only place that works — and it costs nothing, because your little finger wants to be there anyway.

**Ledges locate, slots clamp.** The cell's hole positions vary between suppliers, and the published drawings are bitmaps we cannot measure. Depending on a number we cannot verify would be poor practice, so the design removes the dependency: a 3 mm ledge at each end butts against the cell's end face and sets its position exactly, while the bolts pass through slots covering 8-26 mm and 28-50 mm from the end. Any hole spacing in that range assembles. The bolts are loaded along their own axis here (the squeeze force is parallel to the bolts), not in shear, so a slot is no weaker than a round hole - which is what makes this trick legitimate rather than a bodge.

**The carrier arm is above the top bolts.** The bolts into the cell's top holes are tightened with a hex key coming in along the bolt axis. The arm is placed above them so the key has a clear path. Small thing; it's the difference between assembling in two minutes and not being able to assemble at all.

**The grip is above the cell.** Your fingers wrap the grip from z ≈ 112 to 202 mm. The cell is below 94 mm. Nothing you touch is near the sensor. Single-point cells are designed to read the same regardless of where on the "platform" the load is applied, so loading 40–100 mm above the cell top is inside their design intent.

**There's a hole through the top of the grip.** That's for calibration. Turn the device 90° in a vise, hang a cord through that hole, and the masses pull the grip toward the palm through exactly the path a squeeze uses (R6). The hole is 7 mm above the wall top so the cord clears it.

**The base extends past the grip.** That 30 mm tab is what the vise clamps during calibration.

**Overload stop.** M6 bolt through the wall at z = 80, tip 0.5 mm from the cell's back face. Human grip can't damage a 100 kg cell — this guards against drops and someone leaning on it.

## 4. Why the CAD is a Python script and not a FreeCAD file

You asked whether you should have used FreeCAD. The answer is: you could, and FreeCAD will open the `.step` files we produce. But for this project a script is better, and here is why.

Every dimension in the design depends on the load cell — and load cells from different suppliers vary in length, hole spacing and thread. In a GUI CAD tool, changing the cell means editing a dozen sketches and hoping you caught every dependency. In `dynamometer_cad.py` the cell is six numbers at the top of the file; everything downstream (bolt hole positions, boss heights, carrier plate size, bolt lengths) is *computed*. Change six numbers, run one command, get new STLs.

The other reasons:
- **It's version-controlled properly.** Git can diff a text file. It can't diff a binary CAD file. Your commit history shows *what changed and why*.
- **It's reviewable.** Someone can read the geometry as code.
- **Derived values are printed.** Run the script and it tells you which bolt length to buy.

The tool is **CadQuery** (`pip install cadquery`). It's a Python wrapper over OpenCascade, the same geometry kernel FreeCAD uses. It exports STL for printing and STEP for any CAD program.

**When you'd use FreeCAD instead:** if you want to sculpt a shape by eye, add organic curves, or you're more comfortable dragging than typing. For a bracket-and-bosses design like this one, code wins.

## 5. What was cut, and why

- **Adjustable grip span.** Adds a slider, adds play, adds a place for force to leak. Clinical position 2 is ~48 mm; 50 mm fixed is close enough and rigid.
- **Metal frame.** Was the original plan. Printing removes all cutting and drilling and lets the wall+gusset be one piece.
- **Separate fixed handle rod.** Weak when printed. Replaced by the palm wall.
- **The 80 x 12.7 mm TAL220 bar.** The original choice, and wrong: that form factor only exists up to about 50 kg, and the 100 kg variants are alloy steel and unavailable at retail in Canada. Recorded here because catching a sourcing error before ordering is worth as much as catching a design error.
- **Heat-set inserts.** Nice but one more thing to buy and a soldering-iron technique to learn. The load cell's own threaded holes are the nuts; the only real nut is captive in a printed pocket.
- **Custom PCB, second load cell, pulse sensor, live GUI.** All out of scope for an 8-week build. Listed in "future work".
