"""
proto1b_sculpted.py — the split tube, given a real form.

One revolved outer shape (flared base -> barrel grip -> dome), then split:
  grey  palm half  + base pod (electronics)     bolts to the cell's lower end
  black finger half + dome (calibration hook)   bolts to the cell's upper end
  grey  base cover
3 mm seams between grey and black everywhere.
"""
import os
import cadquery as cq

CT, CW, CL = 22.0, 30.0, 130.0
AX = CT / 2
SEAM = 1.5
R_BORE = 21.6
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_proto1b")
os.makedirs(OUT, exist_ok=True)

# outer profile: (radius, z) from the flared foot up to the dome
PROFILE = [(30.0, -45), (29.4, -40), (27.8, -31), (26.6, -20), (26.2, -9), (26.8, 8),
           (28.2, 32), (29.0, 58), (28.7, 84), (27.4, 110), (26.2, 128), (25.6, 137),
           (23.5, 143), (18.0, 148), (9.0, 151)]
Z_BOT, Z_TOP = -48.0, 151.6


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).center(AX, 0).circle(r).extrude(z1 - z0)


def slot_z(x0, x1, z0, z1, w):
    return (cq.Workplane("YZ").workplane(offset=x0).center(0, (z0 + z1) / 2)
            .slot2D(z1 - z0 + w, w, angle=90).extrude(x1 - x0))


def outer():
    pts = [(AX + r, z) for r, z in PROFILE]
    return (cq.Workplane("XZ").moveTo(AX, Z_BOT).lineTo(AX + 30.0, Z_BOT).lineTo(*pts[0])
            .spline(pts[1:] + [(AX, Z_TOP)], includeCurrent=True).close()
            .revolve(360, (AX, 0, 0), (AX, 10, 0)))


BODY = outer()


def palm():
    grip = BODY.intersect(box(-60, AX - SEAM, -60, 60, -7, 134)).cut(cyl(R_BORE, -8, 135))
    pod = BODY.intersect(box(-60, 80, -60, 60, -44, -7)).cut(cyl(23.0, -45, -6))
    p = grip.union(pod)
    p = p.union(box(-12, 0, -13, 13, 0, 55))          # clamps the cell's lower end
    p = p.union(box(-12, 5, -13, 13, -3, 0))          # ledge the cell stands on
    for lo, hi in ((8, 26), (28, 50)):
        p = p.cut(slot_z(-60, 1, lo, hi, 6.8))
        p = p.cut(slot_z(-60, -13, lo - 3, hi + 3, 12.5))   # counterbore, heads flush
    p = p.cut(box(AX - 7, AX + 7, -40, -18, -30, -21))  # USB port
    for a in (-1, 1):                                   # cover screw pilots
        p = p.cut(cq.Workplane("XY").workplane(offset=-45).center(AX, a * 25.5).circle(1.4).extrude(12))
    return p


def finger():
    grip = BODY.intersect(box(AX + SEAM, 80, -60, 60, -4, 137)).cut(cyl(R_BORE, -5, 137))
    dome = BODY.intersect(box(-60, 80, -60, 60, 137, 160))
    f = grip.union(dome)
    f = f.union(box(CT, CT + 11.6, -13, 13, CL - 55, CL + 3))   # clamps the upper end
    f = f.union(box(CT - 5, CT + 8, -13, 13, CL, CL + 3))       # ledge on the cell's top
    for lo, hi in ((8, 26), (28, 50)):
        f = f.cut(slot_z(CT - 1, 80, CL - hi, CL - lo, 6.8))
        f = f.cut(slot_z(CT + 12.5, 80, CL - hi - 3, CL - lo + 3, 12.5))
    for z in (5, 26, 47, 68):                                   # finger grooves
        f = f.cut(cq.Workplane("XZ").workplane(offset=-40).center(AX + 35.5, z).circle(10.0).extrude(80))
    f = f.cut(cq.Workplane("XZ").workplane(offset=-40).center(AX, 144.0).circle(3.3).extrude(80))  # hook
    return f


def cover():
    c = BODY.intersect(box(-60, 80, -60, 60, Z_BOT - 1, -44))
    for a in (-1, 1):
        c = c.cut(cq.Workplane("XY").workplane(offset=Z_BOT - 1).center(AX, a * 25.5).circle(1.7).extrude(6))
    return c


def cell():
    return box(0, CT, -CW / 2, CW / 2, 0, CL)


if __name__ == "__main__":
    parts = {"palm": palm(), "finger": finger(), "cover": cover(), "cell": cell()}
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.03, angularTolerance=0.1)
        print(f"{n:7s} valid={p.val().isValid()}  {p.val().Volume()/1000:6.1f} cm3")
    fixed = parts["palm"].union(parts["cover"])
    a = parts["finger"].intersect(fixed)
    b = parts["cell"].intersect(fixed.union(parts["finger"]))
    print(f"finger/palm overlap {a.val().Volume() if a.vals() else 0:.3f} mm3   "
          f"cell/parts overlap {b.val().Volume() if b.vals() else 0:.3f} mm3")
    print(f"grip span at the fullest point: {2*29.0:.0f} mm; overall height {Z_TOP-Z_BOT:.0f} mm")
