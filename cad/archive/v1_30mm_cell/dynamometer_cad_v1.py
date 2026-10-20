"""
dynamometer_cad.py — the hand dynamometer, final design ("split grip").

A round, barrel-shaped handle split lengthwise into two halves, with the load cell
standing upright inside.

    PALM HALF   (grey)  half of the grip + the flared base pod. Bolts to the cell's LOWER end.
    FINGER HALF (black) other half of the grip + the dome.      Bolts to the cell's UPPER end.
    COVER       (grey)  closes the electronics pod under the base.

A 3 mm seam separates grey from black everywhere. Squeeze the handle and the halves
try to close that seam; the only thing joining them is the load cell, so the cell
reads the whole force.

Also generated:
    FIT COUPON          the palm half's clamping zone only. Print first, bolt your cell on.
    CALIBRATION CRADLE  a V-block that holds the palm half during calibration.

Load cell: CZL601 / CZL601AC 100 kg single-point, 130 x 30 x 22 mm, 2x M6 per end, 2.0 mV/V.

Coordinates (device standing upright):
    x  palm -> fingers (the squeeze direction)   y  across   z  up
    The cell occupies x 0..22, y -15..15, z 0..130. The grip's axis runs through its centre.

Run:  python dynamometer_cad.py        needs: pip install cadquery
"""
import os
import cadquery as cq

# ======================================================================
# LOAD CELL — measure yours and edit if different
# ======================================================================
CT, CW, CL = 22.0, 30.0, 130.0          # thickness (x), width (y), length (z)
BOLT = 6.0
SLOT_NEAR, SLOT_FAR = (8.0, 26.0), (28.0, 50.0)   # hole windows from each end face
CLAMP = 55.0                            # length clamped at each end
CELL_CAP_KG, CELL_MV_V = 100.0, 2.0

# ======================================================================
# FORM
# ======================================================================
AX = CT / 2                             # grip axis passes through the cell's centre
SEAM = 1.5                              # half the seam; the full seam is 3 mm
GAP = 3.0                               # air around the load cell, everywhere it isn't bolted
R_BORE = 21.6                           # (old round bore — replaced by the pocket below; kept for reference)
# outer profile, (radius, z): flared foot -> waist -> barrel grip -> dome
PROFILE = [(30.0, -45), (29.4, -40), (27.8, -31), (26.6, -20), (26.2, -9), (26.8, 8),
           (28.2, 32), (29.0, 58), (28.7, 84), (27.4, 110), (26.2, 128), (25.6, 137),
           (23.5, 143), (18.0, 148), (9.0, 151)]
Z_BOT, Z_TOP = -48.0, 151.6
Z_POD_TOP = -7.0                        # palm pod ends here
Z_FINGER_BOT = Z_POD_TOP + 3.0          # finger half starts 3 mm above it
Z_PALM_TOP = 134.0                      # palm half ends here
Z_DOME = Z_PALM_TOP + 3.0               # dome starts 3 mm above it
Z_COVER = -44.0
POD_BORE = 23.0
GROOVES_Z = (5.0, 26.0, 47.0, 68.0)     # finger grooves, one per finger
HOOK_Z = 144.0

# ======================================================================
# FASTENERS
# ======================================================================
SLOT_W, CBORE_W = BOLT + 0.8, 12.5
CB_PALM_X = -11.0                       # counterbore floor, palm side
CB_FING_X = CT + 11.0                   # counterbore floor, finger side
M3_PILOT, M3_CLR = 2.8, 3.4

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, z0, z1, cx=AX, cy=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).circle(r).extrude(z1 - z0)


def slot_z(x0, x1, z0, z1, w):
    """Clean single-solid slot, elongated along z, cut along +x."""
    return (cq.Workplane("YZ").workplane(offset=x0).center(0, (z0 + z1) / 2)
            .slot2D(z1 - z0 + w, w, angle=90).extrude(x1 - x0))


def y_bar(xc, zc, r, half=60.0):
    """Cylinder along y — used for grooves and the hook hole."""
    return cq.Workplane("XZ").workplane(offset=-half).center(xc, zc).circle(r).extrude(2 * half)


def wedge_xz(points, y0, y1):
    """Prism from a triangle in the x-z plane, extruded across y."""
    return (cq.Workplane("XZ").polyline(points).close().extrude(-(y1 - y0))
            .translate((0, y0, 0)))


def pocket(z0, z1):
    """The space inside the grip: the load cell's rectangle grown by GAP on every side,
    with corners rounded at radius GAP. That keeps exactly 3 mm of air all round the
    cell, including its corners, and never reaches past the old round bore."""
    return (cq.Workplane("XY").workplane(offset=z0).center(CT / 2, 0)
            .rect(CT + 2 * GAP, CW + 2 * GAP).extrude(z1 - z0)
            .edges("|Z").fillet(GAP))


def outer_body():
    pts = [(AX + r, z) for r, z in PROFILE]
    return (cq.Workplane("XZ").moveTo(AX, Z_BOT).lineTo(AX + 30.0, Z_BOT).lineTo(*pts[0])
            .spline(pts[1:] + [(AX, Z_TOP)], includeCurrent=True).close()
            .revolve(360, (AX, 0, 0), (AX, 10, 0)))


BODY = outer_body()


# ----------------------------------------------------------------------
def palm():
    grip = BODY.intersect(box(-60, AX - SEAM, -60, 60, Z_POD_TOP, Z_PALM_TOP)).cut(
        pocket(Z_POD_TOP - 1, Z_PALM_TOP + 1))
    pod = BODY.intersect(box(-60, 80, -60, 60, Z_COVER, Z_POD_TOP)).cut(
        cyl(POD_BORE, Z_COVER - 1, Z_POD_TOP + 1))
    p = grip.union(pod)
    p = p.union(box(-12, 0, -13, 13, 0, CLAMP))                    # clamps the cell's lower end
    p = p.union(box(-12, 5, -13, 13, -3, 0))                       # ledge the cell stands on
    p = p.union(wedge_xz([(-12, -3), (5, -3), (-12, -20)], -13, 13))  # 45° gusset: supports the ledge
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        p = p.cut(slot_z(-60, 1, lo, hi, SLOT_W))
        p = p.cut(slot_z(-60, CB_PALM_X, lo - 3, hi + 3, CBORE_W))  # heads sit flush
    p = p.cut(box(AX - 7, AX + 7, -40, -18, -30, -21))             # USB port
    for s in (-1, 1):
        p = p.cut(cyl(M3_PILOT / 2, Z_COVER - 1, Z_COVER + 11, cy=s * 25.5))
    return p


def finger():
    grip = BODY.intersect(box(AX + SEAM, 80, -60, 60, Z_FINGER_BOT, Z_DOME)).cut(
        pocket(Z_FINGER_BOT - 1, Z_DOME))
    dome = BODY.intersect(box(-60, 80, -60, 60, Z_DOME, 170))
    f = grip.union(dome)
    f = f.union(box(CT, CT + 11.6, -13, 13, CL - CLAMP, CL + 3))   # clamps the upper end
    f = f.union(box(CT - 5, CT + 8, -13, 13, CL, CL + 3))          # ledge capping the cell
    f = f.union(wedge_xz([(CT + 11.6, CL - CLAMP), (CT + 11.6, CL - CLAMP - 11.6),
                          (CT, CL - CLAMP)], -13, 13))             # 45° chamfer under the boss
    for lo, hi in (SLOT_NEAR, SLOT_FAR):
        f = f.cut(slot_z(CT - 1, 80, CL - hi, CL - lo, SLOT_W))
        f = f.cut(slot_z(CB_FING_X, 80, CL - hi - 3, CL - lo + 3, CBORE_W))
    for z in GROOVES_Z:
        f = f.cut(y_bar(AX + 35.5, z, 10.0))
    f = f.cut(y_bar(AX, HOOK_Z, 3.3))                               # calibration hook
    return f


def cover():
    c = BODY.intersect(box(-60, 80, -60, 60, Z_BOT - 1, Z_COVER))
    for s in (-1, 1):
        c = c.cut(cyl(M3_CLR / 2, Z_BOT - 2, Z_COVER + 1, cy=s * 25.5))
    return c


def fit_coupon():
    """The palm half from the pod rim up to just past the upper slot:
    ledge, gusset, boss, both slots and counterbores. Stands on its own ring."""
    return palm().intersect(box(-60, 80, -60, 60, -20, CL * 0 + SLOT_FAR[1] + 12))


def cradle():
    """V-block for calibration. The device lies palm-half-down in the V; a zip tie
    through the slots holds the base end down. The vise clamps the flat sides."""
    L, W, H, floor = 175.0, 64.0, 34.0, 8.0
    b = box(-W / 2, W / 2, 0, L, 0, H)
    v = (cq.Workplane("XZ").polyline([(0, floor), (-(H - floor) - 2, H + 2), ((H - floor) + 2, H + 2)])
         .close().extrude(-L - 2).translate((0, -1, 0)))
    b = b.cut(v)
    for x in (-W / 2 + 4, W / 2 - 4):
        b = b.cut(box(x - 5, x + 5, 10, 18, 22, 30))               # zip-tie slots, base end
    return b


def cell():
    return box(0, CT, -CW / 2, CW / 2, 0, CL)


def to_bed(p):
    bb = p.val().BoundingBox()
    return p.translate((-bb.xmin, -bb.ymin, -bb.zmin))


# ----------------------------------------------------------------------
if __name__ == "__main__":
    parts = {"palm_half": palm(), "finger_half": finger(), "cover": cover(),
             "fit_coupon": fit_coupon(), "calibration_cradle": cradle()}
    PR = os.path.join(OUT, "print_ready")
    os.makedirs(PR, exist_ok=True)
    print("part                 valid   size (x y z) mm            volume   ~PETG")
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.03, angularTolerance=0.1)
        cq.exporters.export(p, os.path.join(OUT, f"{n}.step"))
        # every part prints in the orientation it's modelled in (upright), just moved to the bed
        cq.exporters.export(to_bed(p), os.path.join(PR, f"{n}_print.stl"),
                            tolerance=0.03, angularTolerance=0.1)
        bb, v = p.val().BoundingBox(), p.val().Volume() / 1000
        print(f"{n:20s} {str(p.val().isValid()):5s}  {bb.xlen:5.0f} x {bb.ylen:4.0f} x {bb.zlen:4.0f}"
              f"   {v:6.1f} cm3   {v*1.27*0.55:4.0f} g")
    cq.exporters.export(cell(), os.path.join(OUT, "load_cell_placeholder.stl"))

    (cq.Assembly()
     .add(parts["palm_half"], name="palm_half", color=cq.Color(0.87, 0.88, 0.90))
     .add(parts["finger_half"], name="finger_half", color=cq.Color(0.17, 0.18, 0.21))
     .add(parts["cover"], name="cover", color=cq.Color(0.87, 0.88, 0.90))
     .add(cell(), name="load_cell", color=cq.Color(0.18, 0.62, 0.54))
     ).save(os.path.join(OUT, "assembly.step"))

    fixed = parts["palm_half"].union(parts["cover"])
    a = parts["finger_half"].intersect(fixed)
    b = cell().intersect(fixed.union(parts["finger_half"]))
    va = a.val().Volume() if a.vals() else 0.0
    vb = b.val().Volume() if b.vals() else 0.0

    flex = box(0, CT, -CW / 2, CW / 2, CLAMP + 5, CL - CLAMP - 5)   # middle of the cell, where it bends
    try:
        clr_palm = flex.val().distance(parts["palm_half"].val())
        clr_fing = flex.val().distance(parts["finger_half"].val())
    except Exception:
        clr_palm = clr_fing = float("nan")
    wall_groove = (AX + 35.5 - 10.0) - (CT + GAP)                   # groove bottom to pocket face

    L_BOLT = 25   # one size for both ends
    bp = (L_BOLT, L_BOLT - (0 - CB_PALM_X))
    bf = (L_BOLT, L_BOLT - (CB_FING_X - CT))
    assert 1.5 * BOLT <= bp[1] <= CT and 1.5 * BOLT <= bf[1] <= CT, "bolt engagement out of range"
    cpk = (5.0 * CELL_MV_V / 19.53) * 8388608.0 / CELL_CAP_KG

    print(f"""
Checks
  finger half / palm side overlap   {va:.3f} mm3   (must be 0 — the halves never touch)
  load cell / printed parts overlap {vb:.3f} mm3   (must be 0)
  load cell bending zone clearance  palm {clr_palm:.2f} mm, finger {clr_fing:.2f} mm  (must be >= {GAP:.0f})
  wall under the finger grooves     {wall_groove:.1f} mm
  grip diameter at the fullest      {2*29.0:.0f} mm  (this is the grip span)
  overall height                    {Z_TOP - Z_BOT:.0f} mm

Bolts
  palm half    M6 x {bp[0]} button head + washer, 2 off  ({bp[1]:.0f} mm into the cell)
  finger half  M6 x {bf[0]} button head + washer, 2 off  ({bf[1]:.0f} mm into the cell)
  cover        M3 x 8 pan head, 2 off

Expected sensitivity  ~{cpk:,.0f} counts/kg (HX711 gain 128, 5 V, {CELL_MV_V} mV/V, {CELL_CAP_KG:.0f} kg)""")
