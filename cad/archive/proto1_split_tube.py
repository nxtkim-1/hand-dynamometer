"""
proto1_split_tube.py — a round grip split lengthwise into a palm half and a finger half.
The load cell stands upright inside. Palm half bolts to its lower end, finger half
to its upper end; a 3 mm seam keeps the halves apart everywhere.
"""
import os
import cadquery as cq

CT, CW, CL = 22.0, 30.0, 130.0      # cell: x thickness, y width, z length
AX = CT / 2                         # tube axis sits on the cell's centre
GAP, R_IN, R_OUT = 3.0, 21.6, 27.0
SEAM = 1.5                          # half-seam each side of the split plane
POD = 33.0                          # electronics pod height under the grip
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_proto1")
os.makedirs(OUT, exist_ok=True)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).center(AX, 0).circle(r).extrude(z1 - z0)


def tube(z0, z1):
    return cyl(R_OUT, z0, z1).cut(cyl(R_IN, z0 - 1, z1 + 1))


def slot_z(x0, x1, z0, z1, w):
    """A clean single-solid slot along z, cut through along +x."""
    return (cq.Workplane("YZ").workplane(offset=x0).center(0, (z0 + z1) / 2)
            .slot2D(z1 - z0 + w, w, angle=90).extrude(x1 - x0))


def palm():
    p = tube(-7, CL + 4).intersect(box(-40, AX - SEAM, -40, 40, -8, CL + 5))
    p = p.union(box(-12, 0, -13, 13, 0, 55))                     # clamps the lower end
    p = p.union(box(-12, 5, -13, 13, -3, 0))                     # ledge under the cell
    pod = cyl(R_OUT, -7 - POD, -7).cut(cyl(R_OUT - 4, -7 - POD - 1, -6))
    p = p.union(pod)
    for lo, hi in ((8, 26), (28, 50)):
        p = p.cut(slot_z(-40, 1, lo, hi, 6.8))
        p = p.cut(slot_z(-40, -12, lo - 3, hi + 3, 12.5))         # counterbore: heads sit flush
    p = p.cut(box(AX - 7, AX + 7, -R_OUT - 1, -R_OUT + 5, -30, -21))  # USB opening
    return p


def finger():
    f = tube(-4, CL + 7).intersect(box(AX + SEAM, 60, -40, 40, -5, CL + 8))
    f = f.union(cyl(R_OUT, CL + 7, CL + 12))                     # top cap
    f = f.union(box(CT, CT + 11.6, -13, 13, CL - 55, CL + 3))    # clamps the upper end
    f = f.union(box(CT - 5, CT + 8, -13, 13, CL, CL + 3))        # ledge on top of the cell
    lug = box(AX - 6, AX + 6, -5, 5, CL + 12, CL + 24)
    lug = lug.cut(cq.Workplane("XZ").workplane(offset=-10).center(AX, CL + 18).circle(3.3).extrude(20))
    f = f.union(lug)                                             # calibration hook
    for lo, hi in ((8, 26), (28, 50)):
        f = f.cut(slot_z(CT - 1, 60, CL - hi, CL - lo, 6.8))
        f = f.cut(slot_z(CT + 12, 60, CL - hi - 3, CL - lo + 3, 12.5))
    return f


def cover():
    return cyl(R_OUT, -7 - POD - 4, -7 - POD)


def cell():
    return box(0, CT, -CW / 2, CW / 2, 0, CL)


if __name__ == "__main__":
    parts = {"palm": palm(), "finger": finger(), "cover": cover(), "cell": cell()}
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.03, angularTolerance=0.12)
    fixed = parts["palm"].union(parts["cover"])
    a = parts["finger"].intersect(fixed)
    b = parts["cell"].intersect(fixed.union(parts["finger"]))
    va = a.val().Volume() if a.vals() else 0.0
    vb = b.val().Volume() if b.vals() else 0.0
    print(f"grip diameter (span): {2*R_OUT:.0f} mm   length of grip: {CL+11:.0f} mm")
    for n, p in parts.items():
        print(f"{n:7s} valid={p.val().isValid()}")
    print(f"finger/palm overlap: {va:.3f} mm3   cell/parts overlap: {vb:.3f} mm3")
