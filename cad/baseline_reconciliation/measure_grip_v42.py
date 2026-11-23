"""Usage: python measure_grip_v42.py ../jamar_v4_2_review/output/jamar_v4_2_review_assembly.step
Independent [GEOMETRIC-ONLY] measurements of the v4.2 assembly STEP (default palm setting)."""
import sys, json, cadquery as cq
a = cq.importers.importStep(sys.argv[1]).solids().vals()
frame, palm, finger, pod, guard, cell = a
fixed = [frame, pod, guard]

def travel_to_contact(moving, others, dx, step=0.1, limit=40.0):
    """Translate `moving` along x by dx*step until it intersects any of `others`. Returns mm, or None if free to `limit`."""
    d = 0.0
    while d <= limit:
        m = moving.translate(cq.Vector(dx * d, 0, 0))
        for o in others:
            if m.intersect(o).Volume() > 1e-3:
                return round(d, 2)
        d += step
    return None

def x_intervals(solid, z, y=0.0):
    """x ranges where a line along x at (y, z) is inside `solid`."""
    line = cq.Solid.makeBox(400, 0.02, 0.02, cq.Vector(-200, y - 0.01, z - 0.01))
    common = line.intersect(solid)
    out = []
    for s in common.Solids():
        b = s.BoundingBox(); out.append((round(b.xmin, 2), round(b.xmax, 2)))
    return sorted(out)

r = {}
# 1. palm bar: free travel in +x (squeeze direction) before it bears on the frame
r["palm_bar_travel_to_frame_plus_x_mm"] = travel_to_contact(palm, [frame], +1, step=0.05, limit=10)
r["palm_bar_travel_to_frame_minus_x_mm"] = travel_to_contact(palm, [frame], -1, step=0.05, limit=10)
# 2. finger part: travel toward palm (-x) before touching any fixed printed part or the palm bar
r["finger_travel_to_fixed_minus_x_mm"] = travel_to_contact(finger, fixed + [palm], -1, step=0.1, limit=40)
r["finger_travel_to_fixed_plus_x_mm"] = travel_to_contact(finger, fixed, +1, step=0.1, limit=40)
# 3/4. sections along x at y=0 for several heights
rows = {}
for z in [5, 20, 40, 60, 80, 90, 95, 110, 125]:
    rows[z] = {"palm": x_intervals(palm, z), "finger": x_intervals(finger, z), "frame": x_intervals(frame, z), "cell": x_intervals(cell, z)}
r["sections_y0"] = rows
print(json.dumps(r, indent=1))
