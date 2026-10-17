"""
design_s.py — symmetric grip dynamometer.

The idea you can see at a glance:
  LIGHT parts = the palm side.  Head shell + palm bar. Bolted to one end of the load cell.
  DARK parts  = the finger side. Front panel + finger bar. Bolted to the other end.
  A 3 mm seam separates light from dark everywhere. Squeeze, and the dark part
  tries to move toward the light part; the only thing joining them is the load cell.

Both handles hang from the centre of the head, so the device is symmetric.
The load cell lies horizontally inside the head (CZL601, 130 x 30 x 22 mm).

x = squeeze axis (palm at -x, fingers at +x)   y = along the head   z = up
Run:  python design_s.py      needs: pip install cadquery
"""
import os
import cadquery as cq

# ---- load cell ------------------------------------------------------
CL, CW, CT = 130.0, 30.0, 22.0          # length (y), width (z), thickness (x)
CLAMP = 55.0
SLOT_NEAR, SLOT_FAR = (8.0, 26.0), (28.0, 50.0)
BOLT = 6.0

# ---- layout ----------------------------------------------------------
GAP = 3.0
REAR = 10.0
WALL = 4.0
PANEL_T = 11.0
CZ0 = 30.0                               # cell underside
BAY = 21.0                               # electronics bay height above the cell
BAR_T = 14.0
BAR_W = 36.0
PALM_LEN = 88.0
FINGER_LEN = 104.0                       # longer: the foot sits below the palm bar
FOOT_H = 12.0
GROOVES = 4

# ---- derived ---------------------------------------------------------
CZ1 = CZ0 + CW
X_REAR = -GAP - REAR                     # palm contact plane
X_FRONT = CT + GAP + PANEL_T             # finger contact plane
Y0, Y1 = -1.0 - WALL, CL + 6.0 + WALL    # head ends
YC = (Y0 + Y1) / 2                       # centre line: both handles hang here
Z_FLOOR = CZ0 - GAP - WALL
Z_TOP = CZ1 + GAP + BAY                  # top of the walls; cover sits on this
COVER_T = 4.0
BY0, BY1 = YC - BAR_W / 2, YC + BAR_W / 2
SPAN = X_FRONT - X_REAR

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_design_s")
os.makedirs(OUT, exist_ok=True)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def fillet(p, sel, r):
    for rr in (r, r * 0.6, r * 0.35):
        try:
            return p.edges(sel).fillet(rr)
        except Exception:
            pass
    return p


def slot_y(x0, x1, y0, y1, zc, w):
    b = box(x0, x1, y0, y1, zc - w / 2, zc + w / 2)
    for y in (y0, y1):
        b = b.union(cq.Workplane("YZ").workplane(offset=x0).center(y, zc).circle(w / 2).extrude(x1 - x0))
    return b


# ---- palm side: head shell + palm bar ------------------------------
def shell():
    s = box(X_REAR, X_FRONT, Y0, Y1, Z_FLOOR, Z_TOP)
    s = fillet(s, "|X", 9.0)
    s = fillet(s, "|Z and <X", 6.0)
    s = s.cut(box(-GAP, X_FRONT + 1, Y0 + WALL, Y1 - WALL, Z_FLOOR + WALL, Z_TOP + 1))
    # floor stops short of the front so the finger side can pass
    s = s.cut(box(CT - GAP, X_FRONT + 1, Y0 + WALL, Y1 - WALL, Z_FLOOR - 1, Z_FLOOR + WALL + 1))
    # fixed-end clamping boss and end stop
    s = s.union(box(-GAP, 0, 0, CLAMP, CZ0, CZ1))
    s = s.union(box(-GAP, 10, -1.0, 0, CZ0, CZ1))
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        s = s.cut(slot_y(X_REAR - 1, 1, lo, hi, (CZ0 + CZ1) / 2, BOLT + 0.8))
        # mirrored blind recess so the back face reads symmetric
        s = s.cut(slot_y(X_REAR - 1, X_REAR + 3, 2 * YC - hi, 2 * YC - lo, (CZ0 + CZ1) / 2, BOLT + 0.8))
    # palm bar, rounded on the back where the palm sits
    bar = box(X_REAR, X_REAR + BAR_T, BY0, BY1, Z_FLOOR - PALM_LEN, Z_FLOOR + 2)
    bar = fillet(bar, "|Z and <X", 6.5)
    bar = fillet(bar, "|Z and >X", 3.0)
    bar = fillet(bar, "<Z", 3.0)
    s = s.union(bar)
    # USB opening in one end wall, cover screw holes in the corners
    s = s.cut(box(0, 14, Y0 - 1, Y0 + WALL + 1, Z_TOP - 15, Z_TOP - 6))
    for y in (Y0 + 12, Y1 - 12):
        s = s.cut(cq.Workplane("XY").workplane(offset=Z_TOP - 10).center(X_REAR + REAR / 2, y)
                  .circle(1.4).extrude(11))
    return s


def cover():
    c = box(X_REAR, X_FRONT, Y0, Y1, Z_TOP, Z_TOP + COVER_T)
    c = fillet(c, "|Z", 9.0)
    c = fillet(c, ">Z", 2.5)
    for y in (Y0 + 12, Y1 - 12):
        c = c.cut(cq.Workplane("XY").workplane(offset=Z_TOP - 1).center(X_REAR + REAR / 2, y)
                  .circle(1.7).extrude(COVER_T + 2))
    return c


# ---- finger side: front panel + finger bar -------------------------
def front():
    zc = (CZ0 + CZ1) / 2
    panel = box(CT + GAP, X_FRONT, Y0 + WALL + GAP, Y1 - WALL - GAP, Z_FLOOR, Z_TOP - GAP)
    panel = fillet(panel, "|X", 4.0)
    boss = box(CT, CT + GAP, CL - CLAMP + 5, CL - 3, CZ0, CZ1)          # touches the free end
    lip = box(CT - 5, CT, CL, CL + 3, CZ0, CZ1)                          # locates on its end face
    bar = box(X_FRONT - BAR_T, X_FRONT, BY0, BY1, Z_FLOOR - FINGER_LEN, Z_FLOOR + 1)
    bar = fillet(bar, "|Z and >X", 6.5)
    bar = fillet(bar, "|Z and <X", 3.0)
    foot = box(X_REAR + BAR_T + 7, X_FRONT, BY0, BY1,
               Z_FLOOR - FINGER_LEN, Z_FLOOR - FINGER_LEN + FOOT_H)
    foot = fillet(foot, "|Z", 3.0)
    f = panel.union(boss).union(lip).union(bar).union(foot)
    # finger grooves across the front of the bar
    top, bot = Z_FLOOR - 8, Z_FLOOR - FINGER_LEN + FOOT_H + 6
    pitch = (top - bot) / GROOVES
    for i in range(GROOVES):
        z = bot + pitch * (i + 0.5)
        f = f.cut(cq.Workplane("XZ").workplane(offset=-(BY1 + 1)).center(X_FRONT + 7.5, z)
                  .circle(10.0).extrude(BAR_W + 2))
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        f = f.cut(slot_y(CT - 1, X_FRONT + 1, CL - hi, CL - lo, zc, BOLT + 0.8))
        # mirrored blind recess so the front face reads symmetric
        f = f.cut(slot_y(X_FRONT - 3, X_FRONT + 1, 2 * YC - (CL - lo), 2 * YC - (CL - hi), zc, BOLT + 0.8))
    # calibration hook through the foot, below the palm bar
    f = f.cut(cq.Workplane("XZ").workplane(offset=-(BY1 + 1))
              .center((X_REAR + BAR_T + 7 + X_FRONT) / 2 + 1, Z_FLOOR - FINGER_LEN + FOOT_H / 2)
              .circle(3.25).extrude(BAR_W + 2))
    return f


def cell():
    return box(0, CT, 0, CL, CZ0, CZ1)


if __name__ == "__main__":
    parts = {"shell": shell(), "cover": cover(), "front": front(), "cell": cell()}
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.03, angularTolerance=0.15)
        bb = p.val().BoundingBox()
        print(f"{n:6s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f} mm   {p.val().Volume()/1000:6.1f} cm3")
    (cq.Assembly()
     .add(parts["shell"], name="palm_shell", color=cq.Color(0.87, 0.88, 0.90))
     .add(parts["cover"], name="cover", color=cq.Color(0.87, 0.88, 0.90))
     .add(parts["front"], name="finger_front", color=cq.Color(0.18, 0.19, 0.22))
     .add(parts["cell"], name="load_cell", color=cq.Color(0.18, 0.62, 0.54))
     ).save(os.path.join(OUT, "assembly_symmetric.step"))

    fixed = parts["shell"].union(parts["cover"])
    ov = parts["front"].intersect(fixed)
    v = ov.val().Volume() if ov.vals() else 0.0
    ov2 = parts["cell"].intersect(fixed.union(parts["front"]))
    v2 = ov2.val().Volume() if ov2.vals() else 0.0
    print(f"\ngrip span, palm face to finger face : {SPAN:.0f} mm")
    print(f"handles centred at y = {YC:.1f} (head runs {Y0:.0f} to {Y1:.0f})")
    print(f"finger side / palm side overlap     : {v:.3f} mm3  (must be 0)")
    print(f"load cell / printed parts overlap   : {v2:.3f} mm3  (must be 0)")
