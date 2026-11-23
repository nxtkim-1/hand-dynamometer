"""Usage: python compare_parts_v41_v42.py <unzipped v4.1 jamar_v4_1_review dir> <unzipped v4.2 print-files dir>
Compare exported v4.1 and v4.2 Jamar CAD parts: STEP solid validity/volume/bbox, STL mesh health.
[GEOMETRIC-ONLY] - says nothing about strength or printed fit."""
import sys, json, hashlib, os
import cadquery as cq, trimesh
v41, v42 = sys.argv[1], sys.argv[2]
parts = ["frame", "palm_bar", "finger_part", "pod_cover", "guard_left"]
stl41 = {"frame":"1_frame","palm_bar":"2_palm_bar","finger_part":"3_finger_bar","pod_cover":"4_pod_cover","guard_left":"5_guard_left"}
out = {}
def step_info(p):
    s = cq.importers.importStep(p)
    solids = s.solids().vals()
    bb = s.val().BoundingBox()
    return {"solids": len(solids), "valid": all(x.isValid() for x in solids),
            "vol_cm3": round(sum(x.Volume() for x in solids)/1000, 2),
            "bbox_mm": [round(bb.xlen,1), round(bb.ylen,1), round(bb.zlen,1)]}
def stl_info(p):
    m = trimesh.load(p, force="mesh")
    return {"watertight": bool(m.is_watertight), "winding_ok": bool(m.is_winding_consistent),
            "vol_cm3": round(m.volume/1000, 2), "extent_mm": [round(e,1) for e in m.extents], "faces": len(m.faces)}
for part in parts:
    r = {}
    for tag, base, ver in [("v4_1", v41, "v4_1"), ("v4_2", v42, "v4_2")]:
        r[tag] = {"step": step_info(os.path.join(base, f"{part}_{ver}.step") if tag=="v4_1" else os.path.join(base, "editable_STEP", f"{part}_{ver}.step")),
                  "print_stl": stl_info(os.path.join(base, "print_ready", f"{stl41[part]}_jamar_{ver}.stl"))}
    out[part] = r
print(json.dumps(out, indent=1))
