"""
design_a.py — Design A, "clinical": modelled on how a Jamar dynamometer is laid out.

    HEAD      a closed housing on top. The load cell lies inside it, horizontal.
    PALM BAR  hangs from the housing. Your palm presses its back face.
    HANDLE    bolts to the load cell's free end and hangs down beside the palm bar.
              Your fingers wrap its front face.
    LID       closes the top of the housing and carries the Nano and HX711.

The rule that makes it measure correctly: the palm bar is part of the housing,
which bolts to one end of the load cell; the handle bolts to the other end; and
the handle touches nothing else. 3 mm of air everywhere between them.

Coordinates:  x  palm -> fingers (the squeeze axis)
              y  along the load cell (left-right when you hold it)
              z  up
Run:  python design_a.py        needs: pip install cadquery
"""
import os
import cadquery as cq

# ---------------- load cell: CZL601 100 kg ---------------------------
CELL_L, CELL_W, CELL_T = 130.0, 30.0, 22.0     # length (y), width (z), thickness (x)
CLAMP = 55.0                                   # length clamped at each end
SLOT_NEAR, SLOT_FAR = (8.0, 26.0), (28.0, 50.0)  # hole windows from each end face
BOLT = 6.0

# ---------------- layout --------------------------------------------
GAP = 3.0            # clearance between moving and fixed parts, everywhere
WALL = 4.0           # housing wall thickness
REAR = 10.0          # rear (palm side) wall thickness
CELL_Z0 = 30.0       # underside of the cell
BAR_T = 14.0         # thickness of each hand bar (x)
BAR_W = 35.0         # width of each hand bar (y)
BAR_Y0 = 85.0        # hand position along y
PALM_BOTTOM = -66.0  # bottom of the palm bar
HANDLE_BOTTOM = -84.0
FOOT_H = 12.0        # finger stop at the bottom of the handle
LID_H = 22.0         # lid height (electronics live inside it)
FR = 6.0             # general edge rounding

# ---------------- derived --------------------------------------------
CX0, CX1 = 0.0, CELL_T                 # cell in x
CY0, CY1 = 0.0, CELL_L                 # cell in y
CZ0, CZ1 = CELL_Z0, CELL_Z0 + CELL_W   # cell in z

HX0 = CX0 - GAP - REAR                 # housing rear face = palm contact plane
HX1 = CX1 + 14.0                       # housing front face, flush with the handle plate
HY0 = CY0 - 1.0 - WALL                 # housing ends
HY1 = CY1 + 7.0 + WALL
HZ0 = CZ0 - GAP - WALL                 # housing underside
HZ1 = CZ1 + GAP                        # housing top rim (lid sits here)
FREE_Y0 = CY1 - CLAMP                  # start of the free-end clamp zone

PLATE_X0, PLATE_X1 = CX1, CX1 + BAR_T  # handle plate against the cell's front face
PLATE_Y0, PLATE_Y1 = FREE_Y0 + 3.0, CY1 + 3.0

PALM_X0, PALM_X1 = HX0, HX0 + BAR_T
SPAN = PLATE_X1 - HX0                  # outer-to-outer grip span

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_design_a")
os.makedirs(OUT, exist_ok=True)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def slot_y(x0, x1, y0, y1, zc, w):
    """A slot elongated along y, cut through along x."""
    body = box(x0, x1, y0, y1, zc - w / 2, zc + w / 2)
    for y in (y0, y1):
        body = body.union(cq.Workplane("YZ").workplane(offset=x0).center(y, zc)
                          .circle(w / 2).extrude(x1 - x0))
    return body


def rounded(part, r):
    for rr in (r, r * 0.6, r * 0.35):
        try:
            return part.edges("|Z or |X").fillet(rr)
        except Exception:
            continue
    return part


# ---------------- housing (palm side) --------------------------------
def housing():
    h = box(HX0, HX1, HY0, HY1, HZ0, HZ1)
    h = rounded(h, 8.0)
    # hollow it out (open top, closed by the lid)
    h = h.cut(box(CX0 - GAP, CX1 + GAP, HY0 + WALL, HY1 - WALL, HZ0 + WALL, HZ1 + 5))
    # free-end zone: open the front wall and the floor so the handle can pass
    h = h.cut(box(CX1 - 1, HX1 + 1, PLATE_Y0 - GAP, PLATE_Y1 + GAP, CZ0 - GAP, HZ1 + 1))
    h = h.cut(box(CX1 - GAP, HX1 + 1, BAR_Y0 - GAP, BAR_Y0 + BAR_W + GAP, HZ0 - 1, CZ0))
    # clamping boss: fills the rear gap only where the fixed end bolts on
    h = h.union(box(CX0 - GAP, CX0, CY0, CY0 + CLAMP, CZ0, CZ1))
    # end stop: the cell's end face butts against this (sets its position)
    h = h.union(box(CX0 - GAP, CX0 + 10, CY0 - 1.0, CY0, CZ0, CZ1))
    # bolt slots through rear wall + boss into the fixed end
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        h = h.cut(slot_y(HX0 - 1, CX0 + 1, CY0 + lo, CY0 + hi, (CZ0 + CZ1) / 2, BOLT + 0.8))
    # palm bar hanging below
    bar = box(PALM_X0, PALM_X1, BAR_Y0, BAR_Y0 + BAR_W, PALM_BOTTOM, HZ0 + 1)
    bar = rounded(bar, FR)
    h = h.union(bar)
    # two M3 holes in the rear wall top for the lid
    for y in (HY0 + 18, HY1 - 18):
        h = h.cut(cq.Workplane("XY").workplane(offset=HZ1 - 10)
                  .center(HX0 + REAR / 2, y).circle(1.4).extrude(11))
    return h


# ---------------- lid (electronics inside) ---------------------------
def lid():
    l = box(HX0, HX1, HY0, HY1, HZ1, HZ1 + LID_H)
    l = rounded(l, 8.0)
    try:
        l = l.faces(">Z").edges().fillet(6.0)
    except Exception:
        pass
    l = l.cut(box(HX0 + 3, HX1 - 3, HY0 + 3, HY1 - 3, HZ1 - 1, HZ1 + LID_H - 3))
    for y in (HY0 + 18, HY1 - 18):
        l = l.cut(cq.Workplane("XY").workplane(offset=HZ1 - 1)
                  .center(HX0 + REAR / 2, y).circle(1.7).extrude(LID_H + 2))
    # USB opening at the left end
    l = l.cut(box(HX0 + 10, HX0 + 24, HY0 - 1, HY0 + 4, HZ1 + 4, HZ1 + 13))
    return l


# ---------------- handle (finger side) -------------------------------
def handle():
    zc = (CZ0 + CZ1) / 2
    plate = box(PLATE_X0, PLATE_X1, PLATE_Y0, PLATE_Y1, CZ0, CZ1)
    lip = box(CX1 - 5, CX1, CY1, CY1 + 3, CZ0, CZ1)          # butts the cell's end face
    neck = box(PLATE_X0, PLATE_X1, BAR_Y0, BAR_Y0 + BAR_W, HZ0 - 8, CZ0 + 1)
    bar = box(PLATE_X0, PLATE_X1, BAR_Y0, BAR_Y0 + BAR_W, HANDLE_BOTTOM, HZ0 - 7)
    foot = box(PALM_X1 + 7, PLATE_X1, BAR_Y0, BAR_Y0 + BAR_W,
               HANDLE_BOTTOM, HANDLE_BOTTOM + FOOT_H)
    h = rounded(plate, 3.0).union(lip).union(neck).union(rounded(bar, FR)).union(rounded(foot, 4.0))
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        h = h.cut(slot_y(PLATE_X0 - 1, PLATE_X1 + 1, CY1 - hi, CY1 - lo, zc, BOLT + 0.8))
    # calibration hook through the foot, below the palm bar so the cord hangs clear
    hook_x = (PALM_X1 + 7 + PLATE_X1) / 2 + 2
    h = h.cut(cq.Workplane("XZ").workplane(offset=-(BAR_Y0 + BAR_W + 5))
              .center(hook_x, HANDLE_BOTTOM + FOOT_H / 2).circle(3.25).extrude(BAR_W + 10))
    return h


def cell():
    return box(CX0, CX1, CY0, CY1, CZ0, CZ1)


if __name__ == "__main__":
    parts = {"housing": housing(), "lid": lid(), "handle": handle(), "cell": cell()}
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.03, angularTolerance=0.15)
        bb = p.val().BoundingBox()
        print(f"{n:8s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f} mm   {p.val().Volume()/1000:6.1f} cm3")
    (cq.Assembly()
     .add(parts["housing"], name="housing", color=cq.Color(0.82, 0.83, 0.86))
     .add(parts["lid"], name="lid", color=cq.Color(0.82, 0.83, 0.86))
     .add(parts["handle"], name="handle", color=cq.Color(0.22, 0.23, 0.26))
     .add(parts["cell"], name="load_cell", color=cq.Color(0.18, 0.62, 0.54))
     ).save(os.path.join(OUT, "assembly_design_a.step"))

    # clearance audit between the two sides: handle vs housing+lid
    fixed = parts["housing"].union(parts["lid"])
    inter = parts["handle"].intersect(fixed)
    vol = inter.val().Volume() if inter.vals() else 0.0
    print(f"\ngrip span (palm face to finger face): {SPAN:.0f} mm")
    print(f"handle / housing overlap volume: {vol:.3f} mm3   (must be 0)")
