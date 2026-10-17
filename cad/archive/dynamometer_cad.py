"""
dynamometer_cad.py — parametric CAD for the hand dynamometer.

TWO PRINTED PARTS. That is the whole device.

    PALM part   bolts to the cell's LOWER end and rises on the palm side
    FINGER part bolts to the cell's UPPER end and hangs on the finger side

They pass each other without ever touching, because they live on opposite
faces of the load cell. Squeeze and they try to close; the only thing joining
them is the cell, so the cell reads the whole force. This is how a clinical
dynamometer works.

                  palm | cell |     | finger
       x  -14 ........ 0 .... 22 .. 24 .... 38
                 <--- grip span 52 --->

Cell: CZL601 / CZL601AC family single-point (parallel beam), 100 kg,
130 x 30 x 22 mm, 2x M6 threaded holes per end, 2.0 mV/V.

TOLERANCE
Hole positions vary between suppliers, so the cell is not located by its bolts:
a LEDGE at each end butts against its end face and sets the position, and the
bolts pass through SLOTS covering 8-26 and 28-50 mm from each end face.

Run:   python dynamometer_cad.py        (needs: pip install cadquery)

Coordinates, device held upright:
  +x  palm toward fingers    +y  across the width    +z  up (toward the thumb)
"""

import math
import os
import cadquery as cq

# ======================================================================
# LOAD CELL — measure yours and edit these five numbers
# ======================================================================
CELL_L = 130.0
CELL_W = 30.0
CELL_T = 22.0
BOLT_D = 6.0
SLOT_NEAR = (8.0, 26.0)     # windows from each end face for the two bolt holes
SLOT_FAR = (28.0, 50.0)

CELL_CAP_KG = 100.0
CELL_MV_V = 2.0

# ======================================================================
# THE DEVICE
# ======================================================================
W = 46.0              # palm part width
FW = 42.0             # finger bar width
PALM_T = 12.0         # palm plate thickness
PALM_BOSS = 2.0       # boss that closes the gap to the cell where it bolts
GAP = 2.0             # clearance, finger bar to cell
FINGER_T = 14.0
CELL_Z0 = 20.0        # cell lower end face
HEAD_H = 19.0         # head block above the cell
HEAD_GAP = 3.0        # clearance, cell top to head block
FINGER_Z0 = 2.0       # bottom of the finger bar (hangs below the palm plate)
GRIP_R = 6.0          # fillet on the gripping surfaces
CLAMP_LEN = 55.0      # length of cell clamped at each end

# ======================================================================
# FASTENERS
# ======================================================================
SLOT_W = BOLT_D + 0.8
STOP_CLR = 6.6
NUT_AF = 10.4
NUT_DEPTH = 5.5
M3_TAP = 2.8
HOOK_D = 6.5
LEDGE_T = 3.0
LEDGE_X = 5.0

# ======================================================================
# DERIVED
# ======================================================================
CELL_X0, CELL_X1 = 0.0, CELL_T
CELL_Z1 = CELL_Z0 + CELL_L

PALM_X0 = -PALM_T - PALM_BOSS          # -14 : the palm contact face
PALM_X1 = -PALM_BOSS                   # -2  : back of the plate, clear of the cell
BOSS_Z0 = CELL_Z0 - LEDGE_T
BOSS_Z1 = CELL_Z0 + CLAMP_LEN

HEAD_Z0 = CELL_Z1 + HEAD_GAP           # 153
HEAD_Z1 = HEAD_Z0 + HEAD_H             # 172
HEAD_X1 = 20.0

FING_BOSS_X0 = CELL_X1                 # 22, touches the cell
FING_BAR_X0 = CELL_X1 + GAP            # 24, clears it
FING_X1 = FING_BAR_X0 + FINGER_T       # 38
FING_BOSS_Z0 = CELL_Z1 - CLAMP_LEN     # 95
FING_Z1 = HEAD_Z1                      # 172

GRIP_SPAN = FING_X1 - PALM_X0
STOP_Z = (HEAD_Z0 + HEAD_Z1) / 2.0
HOOK_Z = FINGER_Z0 + 8.0
YC = W / 2.0

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)

assert PALM_X1 < CELL_X0, "palm plate would rub the cell"
assert FING_BAR_X0 > CELL_X1, "finger bar would rub the cell"
assert HEAD_X1 < FING_BOSS_X0, "head block would touch the finger part"
assert HOOK_Z < BOSS_Z0, "calibration cord would be blocked by the palm part"


def hexd(af):
    return af / math.cos(math.radians(30))


def prof(points, width, y0):
    s = cq.Workplane("XZ").polyline(points).close().extrude(-width)
    bb = s.val().BoundingBox()
    return s.translate((0, y0 - bb.ymin, 0))


def slot(x0, length, z_lo, z_hi, yc=None):
    """Bolt slot running along z, cut through along +x."""
    yc = YC if yc is None else yc
    r = SLOT_W / 2.0
    b = (cq.Workplane("YZ").workplane(offset=x0).center(yc, (z_lo + z_hi) / 2.0)
         .rect(SLOT_W, z_hi - z_lo).extrude(length))
    for z in (z_lo, z_hi):
        b = b.union(cq.Workplane("YZ").workplane(offset=x0).center(yc, z)
                    .circle(r).extrude(length))
    return b


def round_edges(part, sel, r):
    try:
        return part.edges(cq.selectors.BoxSelector(*sel)).fillet(r)
    except Exception:
        return part


# ----------------------------------------------------------------------
def palm():
    """Palm plate + mounting boss + head block. Bolts to the cell's lower end."""
    pts = [(PALM_X0, CELL_Z0), (PALM_X1, CELL_Z0), (PALM_X1, HEAD_Z0),
           (HEAD_X1, HEAD_Z0), (HEAD_X1, HEAD_Z1), (PALM_X0, HEAD_Z1)]
    p = prof(pts, W, 0)

    # boss: closes the 2 mm gap so the plate meets the cell where it bolts
    p = p.union(cq.Workplane("XY").box(PALM_BOSS, CELL_W + 6.0, BOSS_Z1 - BOSS_Z0,
                                       centered=False)
                .translate((PALM_X1, YC - (CELL_W + 6.0) / 2, BOSS_Z0)))
    # ledge: the cell's lower end face rests on this
    p = p.union(cq.Workplane("XY").box(PALM_BOSS + LEDGE_X, CELL_W + 6.0, LEDGE_T,
                                       centered=False)
                .translate((PALM_X1, YC - (CELL_W + 6.0) / 2, BOSS_Z0)))

    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        p = p.cut(slot(PALM_X0 - 1, PALM_T + PALM_BOSS + 2,
                       CELL_Z0 + lo, CELL_Z0 + hi))

    # two M3 holes on the back of the head for the electronics tray
    for z in (HEAD_Z0 + 5, HEAD_Z1 - 5):
        p = p.cut(cq.Workplane("YZ").workplane(offset=PALM_X0 - 1).center(YC, z)
                  .circle(M3_TAP / 2).extrude(8))

    p = round_edges(p, ((PALM_X0 - 1, -1, CELL_Z0 + 2), (PALM_X0 + 1, W + 1, HEAD_Z1 - 2)), 5.0)
    p = round_edges(p, ((PALM_X0 - 1, -1, HEAD_Z1 - 1), (HEAD_X1 + 1, W + 1, HEAD_Z1 + 1)), 4.0)
    return p


def finger():
    """Finger bar + upper boss. Bolts to the cell's upper end."""
    pts = [(FING_BAR_X0, FINGER_Z0), (FING_X1, FINGER_Z0), (FING_X1, FING_Z1),
           (FING_BOSS_X0, FING_Z1), (FING_BOSS_X0, FING_BOSS_Z0),
           (FING_BAR_X0, FING_BOSS_Z0)]
    f = prof(pts, FW, YC - FW / 2)

    # ledge capping the cell's upper end face
    f = f.union(cq.Workplane("XY").box(LEDGE_X + GAP, FW, LEDGE_T, centered=False)
                .translate((CELL_X1 - LEDGE_X, YC - FW / 2, CELL_Z1)))

    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        f = f.cut(slot(CELL_X1 - 1, FINGER_T + GAP + 2,
                       CELL_Z1 - hi, CELL_Z1 - lo))

    # overload stop: bolt threads in from the outside, above the grip zone
    f = f.cut(cq.Workplane("YZ").workplane(offset=FING_X1 + 1).center(YC, STOP_Z)
              .circle(STOP_CLR / 2).extrude(-(FING_X1 - HEAD_X1 + 2)))
    f = f.cut(cq.Workplane("YZ").workplane(offset=FING_X1 + 0.01).center(YC, STOP_Z)
              .polygon(6, hexd(NUT_AF)).extrude(-NUT_DEPTH - 0.01))

    # calibration hook, below everything else so the cord hangs free
    f = f.cut(cq.Workplane("XZ").workplane(offset=-W).center(
        (FING_BAR_X0 + FING_X1) / 2, HOOK_Z).circle(HOOK_D / 2).extrude(2 * W))

    # round the gripping surfaces generously
    f = round_edges(f, ((FING_BAR_X0 - 1, -1, FINGER_Z0 - 1),
                        (FING_X1 + 1, W + 1, FING_BOSS_Z0 - 2)), GRIP_R)
    return f


def tray():
    """Electronics tray, screws to the back of the head block."""
    L, H, t, d = 46.0, HEAD_H, 2.0, 22.0
    b = (cq.Workplane("XY").box(d, L, H, centered=False)
         .translate((PALM_X0 - d, YC - L / 2, HEAD_Z0)))
    b = b.cut(cq.Workplane("XY").box(d - t, L - 2 * t, H - t, centered=False)
              .translate((PALM_X0 - d + t, YC - L / 2 + t, HEAD_Z0 + t)))
    for z in (HEAD_Z0 + 5, HEAD_Z1 - 5):
        b = b.cut(cq.Workplane("YZ").workplane(offset=PALM_X0 - t - 1).center(YC, z)
                  .circle(3.4 / 2).extrude(t + 2))
    b = b.cut(cq.Workplane("XY").box(10.0, t + 2, 9.0, centered=False)
              .translate((PALM_X0 - d + 6, YC - L / 2 - 1, HEAD_Z1 - 9.0)))
    return b


def cell_model():
    return (cq.Workplane("XY").box(CELL_T, CELL_W, CELL_L, centered=False)
            .translate((CELL_X0, YC - CELL_W / 2, CELL_Z0)))


def fit_coupon():
    """A slice of the palm part: ledge, boss and both slots.
    Print this first and bolt your cell to it before printing anything else."""
    z0, z1 = BOSS_Z0 - 4.0, CELL_Z0 + SLOT_FAR[1] + 12.0
    c = (cq.Workplane("XY").box(PALM_T, W, z1 - z0, centered=False)
         .translate((PALM_X0, 0, z0)))
    c = c.union(cq.Workplane("XY").box(PALM_BOSS, CELL_W + 6.0, BOSS_Z1 - BOSS_Z0,
                                       centered=False)
                .translate((PALM_X1, YC - (CELL_W + 6.0) / 2, BOSS_Z0)))
    c = c.union(cq.Workplane("XY").box(PALM_BOSS + LEDGE_X, CELL_W + 6.0, LEDGE_T,
                                       centered=False)
                .translate((PALM_X1, YC - (CELL_W + 6.0) / 2, BOSS_Z0)))
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        c = c.cut(slot(PALM_X0 - 1, PALM_T + PALM_BOSS + 2,
                       CELL_Z0 + lo, CELL_Z0 + hi))
    return c


def print_oriented(p):
    """Lay the part down so the build direction is x: layers then run in the
    y-z plane and the bending stress stays inside them."""
    p = p.rotate((0, 0, 0), (0, 1, 0), 90)
    bb = p.val().BoundingBox()
    return p.translate((-bb.xmin, -bb.ymin, -bb.zmin))


# ----------------------------------------------------------------------
if __name__ == "__main__":
    parts = {"palm": palm(), "finger": finger(),
             "tray": tray(), "fit_coupon": fit_coupon()}

    for name, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{name}.stl"),
                            tolerance=0.02, angularTolerance=0.1)
        cq.exporters.export(p, os.path.join(OUT, f"{name}.step"))
        bb = p.val().BoundingBox()
        print(f"{name:11s} {bb.xlen:6.1f} x {bb.ylen:5.1f} x {bb.zlen:6.1f} mm"
              f"   {p.val().Volume()/1000:6.1f} cm^3")

    PR = os.path.join(OUT, "print_ready")
    os.makedirs(PR, exist_ok=True)
    for name, p in parts.items():
        q = print_oriented(p)
        cq.exporters.export(q, os.path.join(PR, f"{name}_print.stl"),
                            tolerance=0.02, angularTolerance=0.1)
        bb = q.val().BoundingBox()
        print(f"  print_ready/{name}_print.stl   bed {bb.xlen:5.0f} x {bb.ylen:5.0f} mm,"
              f" height {bb.zlen:4.0f} mm")

    (cq.Assembly()
     .add(parts["palm"], name="palm", color=cq.Color(0.80, 0.81, 0.84))
     .add(parts["finger"], name="finger", color=cq.Color(0.66, 0.68, 0.73))
     .add(parts["tray"], name="tray", color=cq.Color(0.58, 0.60, 0.65))
     .add(cell_model(), name="load_cell", color=cq.Color(0.18, 0.62, 0.54))
     ).save(os.path.join(OUT, "assembly.step"))
    cq.exporters.export(cell_model(), os.path.join(OUT, "load_cell_placeholder.stl"))

    STOCK = [10, 12, 16, 20, 25, 30, 35, 40, 45, 50]

    def pick(reach, dia, depth):
        for L in STOCK:
            e = L - reach
            if e >= 1.5 * dia and e <= depth:
                return L, e
        return None

    bp = pick(PALM_T + PALM_BOSS, BOLT_D, CELL_T)
    bf = pick(FINGER_T + GAP, BOLT_D, CELL_T)
    fs = 5.0 * CELL_MV_V
    cpk = (fs / 19.53) * 8388608.0 / CELL_CAP_KG

    print(f"""
The device
  overall           {FING_X1 - (PALM_X0 - 22):.0f} x {W:.0f} x {HEAD_Z1 - FINGER_Z0:.0f} mm, handheld
  grip span         {GRIP_SPAN:.0f} mm, palm face to finger face
  grip zone         z {FINGER_Z0:.0f}..{FING_BOSS_Z0:.0f}  ({FING_BOSS_Z0 - FINGER_Z0:.0f} mm of finger bar)
  cell              x {CELL_X0:.0f}..{CELL_X1:.0f}   z {CELL_Z0:.0f}..{CELL_Z1:.0f}
  palm slots        z {CELL_Z0+SLOT_NEAR[0]:.0f}..{CELL_Z0+SLOT_NEAR[1]:.0f} and {CELL_Z0+SLOT_FAR[0]:.0f}..{CELL_Z0+SLOT_FAR[1]:.0f}
  finger slots      z {CELL_Z1-SLOT_FAR[1]:.0f}..{CELL_Z1-SLOT_FAR[0]:.0f} and {CELL_Z1-SLOT_NEAR[1]:.0f}..{CELL_Z1-SLOT_NEAR[0]:.0f}
  overload stop     z {STOP_Z:.0f}, above the grip zone
  calibration hook  z {HOOK_Z:.0f}, below the palm plate so the cord hangs clear

Bolts to buy
  palm end    M{BOLT_D:.0f} x {bp[0]:.0f} mm, 2 off + 2 washers   ({bp[1]:.0f} mm thread engagement)
  finger end  M{BOLT_D:.0f} x {bf[0]:.0f} mm, 2 off + 2 washers   ({bf[1]:.0f} mm engagement)
  stop        M6 x 25 + 1 nut          tray  M3 x 12, 2 off
  Washers required: the bolts pass through slots, not round holes.

Expected electrical
  {fs:.0f} mV full scale at 5 V ({CELL_MV_V:.1f} mV/V, {CELL_CAP_KG:.0f} kg)
  -> about {cpk:,.0f} counts per kg on an HX711 at gain 128""")
