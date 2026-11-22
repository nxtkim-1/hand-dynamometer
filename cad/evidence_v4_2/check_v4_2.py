"""
check_v4_2.py - reproducible, read-only geometry checks of the PRINTED v4.2 design.  [GEOMETRIC-ONLY]

It never modifies or re-exports the design. It reads the exported files in ../jamar_v4_2_review/output/,
imports the v4.2 source only to rebuild the palm bar in memory at each of the 5 settings, and writes:
    check_v4_2_report.json      every check, value and pass/fail
    inspection_sheet.csv        features to measure on the printed parts (nominal values from the source)

Passing says the files are self-consistent. It says nothing about strength, printed accuracy or safety.

Run from this folder with the CadQuery environment (cadquery, trimesh):
    python check_v4_2.py
    python check_v4_2.py --bed 240 240 250        # bed X Y Z in mm (default: 240 x 240 x 250, Z assumed)
"""
import argparse
import csv
import json
import os
import sys

import cadquery as cq
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
V42 = os.path.join(HERE, "..", "jamar_v4_2_review")
OUT = os.path.join(V42, "output")
sys.path.insert(0, V42)
sys.path.insert(0, os.path.join(HERE, ".."))

PARTS = ["frame", "palm_bar", "finger_part", "pod_cover", "guard_left"]
PRINT = {"frame": "1_frame", "palm_bar": "2_palm_bar", "finger_part": "3_finger_bar",
         "pod_cover": "4_pod_cover", "guard_left": "5_guard_left"}

ap = argparse.ArgumentParser()
ap.add_argument("--bed", nargs=3, type=float, default=[240, 240, 250], metavar=("X", "Y", "Z"))
args = ap.parse_args()
checks = []


def check(name, ok, value, note=""):
    checks.append({"check": name, "pass": bool(ok), "value": value, "note": note})
    print(f"{'PASS' if ok else 'FAIL'}  {name:58} {value}  {note}")


# ---- 1. exported parts: valid solids, healthy meshes, STEP and STL agree ----
steps = {}
for p in PARTS:
    shape = cq.importers.importStep(os.path.join(OUT, f"{p}_v4_2.step"))
    solids = shape.solids().vals()
    steps[p] = solids[0]
    vol_step = sum(s.Volume() for s in solids) / 1000
    check(f"{p}: single valid STEP solid", len(solids) == 1 and solids[0].isValid(), f"{len(solids)} solid(s)")
    m = trimesh.load(os.path.join(OUT, "print_ready", f"{PRINT[p]}_jamar_v4_2.stl"), force="mesh")
    check(f"{p}: print STL watertight + consistent winding", m.is_watertight and m.is_winding_consistent,
          f"{len(m.faces)} faces")
    diff = abs(m.volume / 1000 - vol_step) / vol_step * 100
    check(f"{p}: STL volume matches STEP (< 1 %)", diff < 1.0, f"{diff:.2f} %")
    ext = sorted(m.extents[:2])
    bed_xy = sorted(args.bed[:2])
    check(f"{p}: fits bed lying flat as exported", ext[0] <= bed_xy[0] and ext[1] <= bed_xy[1] and m.extents[2] <= args.bed[2],
          f"{m.extents[0]:.1f} x {m.extents[1]:.1f} x {m.extents[2]:.1f} mm")
    check(f"{p}: lies flat (min z = 0)", abs(m.bounds[0][2]) < 0.01, f"min z {m.bounds[0][2]:.3f}")

for f in sorted(os.listdir(os.path.join(OUT, "combined_plates"))):
    m = trimesh.load(os.path.join(OUT, "combined_plates", f), force="mesh")
    check(f"plate {f[:44]}: within {args.bed[0]:.0f} x {args.bed[1]:.0f}",
          m.extents[0] <= args.bed[0] and m.extents[1] <= args.bed[1] and m.extents[2] <= args.bed[2],
          f"{m.extents[0]:.1f} x {m.extents[1]:.1f} x {m.extents[2]:.1f} mm")

# ---- 2. the assembly: no printed part touches another, the cell carries all force ----
asm = cq.importers.importStep(os.path.join(OUT, "jamar_v4_2_review_assembly.step")).solids().vals()
frame, palm, finger, pod, guard, cell = asm
named = {"frame": frame, "palm_bar": palm, "finger_part": finger, "pod_cover": pod, "guard_left": guard}
names = list(named)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        v = named[a].intersect(named[b]).Volume()
        check(f"no overlap {a} / {b}", v < 1e-3, f"{v:.4f} mm3")


def travel(moving, others, dx, step, limit):
    d = 0.0
    while d <= limit:
        mv = moving.translate(cq.Vector(dx * d, 0, 0))
        if any(mv.intersect(o).Volume() > 1e-3 for o in others):
            return round(d, 2)
        d += step
    return None


t = travel(finger, [frame, pod, guard, palm], -1, 0.1, 40)
check("finger part: free travel toward palm before touching a fixed part", t is not None and t >= 3.0, f"{t} mm",
      "cell deflects < 1 mm at full scale, so >= 3 mm means no force bypass on the squeeze axis")

# ---- 3. all 5 palm settings: rebuilt from source (in memory), checked against the exported frame ----
import jamar_v4_2_review as J  # noqa: E402  (also sets D.CBORE_W = 12.8, as the design does)
import dynamometer_cad as D  # noqa: E402

rebuilt_default = J.palm_bar(J.POS).val()
dv = abs(rebuilt_default.Volume() - palm.Volume()) / palm.Volume() * 100
check("source rebuilds the exported palm bar (setting 2)", dv < 0.1, f"volume diff {dv:.3f} %",
      "shows the editable source matches what was printed")
for pos, span in enumerate(J.OUTER_SPANS):
    pb = J.palm_bar(pos).val()
    ov = max(pb.intersect(o).Volume() for o in (frame, finger, cell))
    check(f"setting {pos + 1} ({span:.0f} mm): palm bar overlaps nothing", ov < 1e-3, f"{ov:.4f} mm3")
    seat = travel(pb, [frame], +1, 0.05, 5)
    check(f"setting {pos + 1}: keyed seat bears on frame before the bolts", seat is not None and seat <= 0.5,
          f"{seat} mm free travel in +x")

# ---- 4. inspection sheet for the printed parts (replaces fit coupons, since the parts are printed) ----
rows = [
    ("frame", "M6 counterbore diameter (x6, cell mounts)", D.CBORE_W, "12.0 mm washer", "12.2 - 13.0", "washer drops in flat"),
    ("frame", "M6 clearance hole diameter", D.HOLE_CLR, "M6 bolt", "6.3 - 7.4", "bolt passes without force"),
    ("finger_part", "M6 counterbore diameter (x3)", D.CBORE_W, "12.0 mm washer", "12.2 - 13.0", "washer drops in flat"),
    ("frame", "keyed palm pocket width (x2 per setting)", J.KEY_POCKET_W, f"{J.KEY_LUG_W} mm lug", "3.5 - 4.1",
     "lug slides in, side play < 0.5 mm"),
    ("frame", "keyed palm pocket depth", J.KEY_POCKET_D, f"{J.KEY_LUG_H} mm lug", ">= 3.0", "lug never bottoms out"),
    ("palm_bar", "key lug width", J.KEY_LUG_W, f"{J.KEY_POCKET_W} mm pocket", "3.1 - 3.6", ""),
    ("palm_bar", "M5 nut slot width", J.NUT_W, "M5 nut AF 8.0", "8.2 - 9.0", "nut slides in, cannot spin"),
    ("palm_bar", "M5 nut slot height", J.NUT_H, "M5 nut 4.7 tall", "4.9 - 5.9", ""),
    ("frame + palm_bar", "M5 clearance hole", J.M5_CLR, "M5 x 30 bolt", "5.2 - 5.8", "bolt passes without force"),
    ("pod_cover + guard", "M3 screw well diameter", J.WELL_D, "pan head <= 6.0 + driver", ">= 6.5", "driver reaches the head"),
    ("pod_cover + guard", "M3 through-hole", J.M3_CLR_V42, "M3 x 10", "3.2 - 3.8", ""),
    ("frame", "M3 self-tap pilot", J.M3_PILOT_V42, "M3 thread", "2.5 - 2.9",
     "UNTESTED in PETG: drive one screw by hand first, stop if the boss cracks"),
    ("assembly", "finger part to frame air gap (all sides)", 3.2, "moving vs fixed", ">= 2.5",
     "slide paper through; any rubbing = force bypass"),
]
with open(os.path.join(HERE, "inspection_sheet.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["part", "feature", "nominal_mm", "mates_with", "accept_mm", "how_to_judge", "measured_mm", "pass"])
    for r in rows:
        w.writerow([r[0], r[1], f"{r[2]:.2f}", r[3], r[4], r[5], "", ""])

failed = [c for c in checks if not c["pass"]]
with open(os.path.join(HERE, "check_v4_2_report.json"), "w", encoding="utf-8") as f:
    json.dump({"tag": "GEOMETRIC-ONLY", "bed_mm": args.bed, "bed_z_note": "Z limit assumed, not measured",
               "n_checks": len(checks), "n_failed": len(failed), "checks": checks}, f, indent=1)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks pass. Wrote check_v4_2_report.json and inspection_sheet.csv")
sys.exit(1 if failed else 0)
