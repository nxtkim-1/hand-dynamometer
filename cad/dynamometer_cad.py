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

Load cell (MEASURED 2026-10-12, see docs/06_build_log.md): 100 kg parallel beam, 130 x 40 x 22 mm,
3x M6 through-tapped holes per end, 33 mm end blocks, 2.0 mV/V.
v1 (built for a 130 x 30 x 22 cell) is kept in archive/v1_30mm_cell/.

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
CT, CW, CL = 22.0, 40.0, 130.0          # thickness (x), width (y), length (z)   measured
BOLT = 6.0                              # M6, through-tapped (checked with a bolt)
BLOCK = 33.0                            # end block length                        measured
HOLE_D = 6.67                           # tapped-hole opening (derived: 40 - 2 x 16.67)
SINGLE_Z = 21.44 + HOLE_D / 2           # single hole centre, from the end face    measured edge + D/2
PAIR_Z = 11.8                           # pair centre, from the end face           measured
PAIR_DY = (7.94 + HOLE_D) / 2           # pair half-spacing across the width       measured gap + D
# the three holes at each end: (z measured from that end's face, y)
HOLES_NEAR = [(PAIR_Z, +PAIR_DY), (PAIR_Z, -PAIR_DY), (SINGLE_Z, 0.0)]
CLAMP = 32.0                            # boss length (end block is 33; stop 1 mm short of the thin web)
BY = 17.0                               # boss / ledge half-width (counterbores reach +-13.6)
CABLE_D = 5.13                          # cable leaves the +y side face, 3.0 mm from the end face, mid-thickness
CELL_CAP_KG, CELL_MV_V = 100.0, 2.0

# ======================================================================
# FORM
# ======================================================================
AX = CT / 2                             # grip axis passes through the cell's centre
SEAM = 1.5                              # half the seam; the full seam is 3 mm
GAP = 3.0                               # air around the load cell, everywhere it isn't bolted
R_BORE = 21.6                           # (old round bore — replaced by the pocket below; kept for reference)
# outer profile, (radius, z): flared foot -> waist -> barrel grip -> dome
# Option B ("roomy round"): radius never below 28.3 along the cell, so the 40 mm cell keeps 3 mm all round
# with >= 2.5 mm of wall at the pocket corners. Pod region (z < -7) unchanged until the pod is redesigned.
PROFILE = [(30.0, -45), (29.4, -40), (28.9, -31), (28.7, -20), (28.5, -9), (28.6, 8),
           (29.0, 32), (29.4, 58), (29.2, 84), (28.8, 110), (28.5, 128), (27.8, 137),
           (24.5, 143), (18.5, 148), (9.0, 151)]
Z_BOT, Z_TOP = -48.0, 151.6
Z_POD_TOP = -7.0                        # palm pod ends here
Z_FINGER_BOT = Z_POD_TOP + 3.0          # finger half starts 3 mm above it
Z_PALM_TOP = 134.0                      # palm half ends here
Z_DOME = Z_PALM_TOP + 3.0               # dome starts 3 mm above it
Z_COVER = -44.0                         # top face of the cover = floor of the electronics bay
POD_BORE = 25.0                         # P1: round bay, diameter 50 (was 46; the Nano needs 47.6)
LEGACY_BORE, LEGACY_XL = 23.0, -12.0    # the released fit coupon was cut with these; it stays byte-for-byte the same

# ======================================================================
# ELECTRONICS BAY  (Nano measured 2026-10-12; HX711 is the nominal 24 x 16 board, NOT measured)
# ======================================================================
NANO_L, NANO_W, PCB_T = 44.0, 18.11, 1.6   # board only, USB connector adds 2 mm at one end
NANO_PIN, NANO_ROW = 8.0, 15.24           # pins stick out 8 mm each side; header rows 15.24 apart
NANO_USB_H = 3.8                          # connector height above the board
RAIL_H = NANO_PIN + 1.5                   # the board rides on a central rail; the lower pins hang beside it
PCB_BOT = Z_COVER + RAIL_H                # -34.5
PCB_TOP = PCB_BOT + PCB_T                 # -32.9
USB_ZC = PCB_TOP + NANO_USB_H / 2         # connector centre height
WIN_W, WIN_H = 14.0, 11.0                 # USB window (mini-B plug moulding is about 10 x 8; generous)
HX_TALL, HX_ACROSS, HX_T = 24.0, 16.0, 4.0 # HX711 stands on its 16 mm edge, board plane = y-z, pads on the +-y edges
HX_XC, HX_SLOT = 26.5, 4.6                # centre x and slot gap between its two rails
BOSS_R = 3.4                              # M3 screw bosses for the cover
BOSSES = [(-8.5, -12.0), (30.5, 12.0)]    # diagonal pair, clear of the Nano and the HX711 rails
EYE = (AX, 21.5)                          # wire eyelet: vertical hole the cell wires pass through (clamp / strain relief)
GROOVES_Z = (5.0, 26.0, 47.0, 68.0)     # finger grooves, one per finger
HOOK_Z = 144.0

# ======================================================================
# FASTENERS
# ======================================================================
HOLE_CLR, CBORE_W = BOLT + 1.2, 12.5   # 7.2 mm clearance holes (the cell was measured, not assumed)
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


def bolt_hole(x0, x1, y, z, d):
    """Round hole along x at (y, z)."""
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(d / 2).extrude(x1 - x0)


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
def palm(bore=POD_BORE, xl=-16.0, bay=True, eyelet=True):
    """bore/xl/bay let the fit coupon keep the geometry that was released (legacy bore, no bay features).
    eyelet=False drops the R1 wire eyelet block (the no-cut cable plan does not use it)."""
    grip = BODY.intersect(box(-60, AX - SEAM, -60, 60, Z_POD_TOP, Z_PALM_TOP)).cut(
        pocket(Z_POD_TOP - 1, Z_PALM_TOP + 1))
    pod = BODY.intersect(box(-60, 80, -60, 60, Z_COVER, Z_POD_TOP)).cut(
        cyl(bore, Z_COVER - 1, Z_POD_TOP + 1))
    p = grip.union(pod)
    # boss, ledge and gusset reach the pod wall (xl); clipped to the body so they never poke out of the barrel
    feat = box(-12, 0, -BY, BY, 0, CLAMP)                           # clamps the cell's lower end
    feat = feat.union(box(xl, 5, -BY, BY, -3, 0))                   # ledge the cell stands on
    feat = feat.union(wedge_xz([(xl, -3), (5, -3), (xl, -3 + (xl - 5))], -BY, BY))  # 45 deg gusset under the ledge
    p = p.union(feat.intersect(BODY) if bay else feat)
    for z, y in HOLES_NEAR:                                         # one bolt per cell hole
        p = p.cut(bolt_hole(-60, 1, y, z, HOLE_CLR))
        p = p.cut(bolt_hole(-60, CB_PALM_X, y, z, CBORE_W))         # heads sit flush
    if not bay:
        return p
    # --- electronics bay ---------------------------------------------------
    for bx, by in BOSSES:                                           # M3 screw bosses for the cover
        p = p.union(cyl(BOSS_R, Z_COVER, Z_COVER + 16, cx=bx, cy=by))
        p = p.cut(cyl(M3_PILOT / 2, Z_COVER - 1, Z_COVER + 10, cx=bx, cy=by))
    if eyelet:
        eye = box(EYE[0] - 5, EYE[0] + 5, 17.5, 26.5, -17, -9)      # wire eyelet block, fused to the bore wall
        p = p.union(eye).cut(cyl(2.3, -18, -8, cx=EYE[0], cy=EYE[1]))  # 4.6 mm hole
    p = p.cut(box(AX - WIN_W / 2, AX + WIN_W / 2, -40, -18, USB_ZC - WIN_H / 2, USB_ZC + WIN_H / 2))  # USB window
    return p


def finger():
    grip = BODY.intersect(box(AX + SEAM, 80, -60, 60, Z_FINGER_BOT, Z_DOME)).cut(
        pocket(Z_FINGER_BOT - 1, Z_DOME))
    dome = BODY.intersect(box(-60, 80, -60, 60, Z_DOME, 170))
    f = grip.union(dome)
    f = f.union(box(CT, CT + 11.6, -BY, BY, CL - CLAMP, CL + 3))   # clamps the upper end
    f = f.union(box(CT - 5, CT + 8, -BY, BY, CL, CL + 3))          # ledge capping the cell
    f = f.union(wedge_xz([(CT + 11.6, CL - CLAMP), (CT + 11.6, CL - CLAMP - 11.6),
                          (CT, CL - CLAMP)], -BY, BY))             # 45° chamfer under the boss
    for z, y in HOLES_NEAR:                                         # same pattern, mirrored end for end
        f = f.cut(bolt_hole(CT - 1, 80, y, CL - z, HOLE_CLR))
        f = f.cut(bolt_hole(CB_FING_X, 80, y, CL - z, CBORE_W))
    for z in GROOVES_Z:
        f = f.cut(y_bar(AX + 35.5, z, 10.0))
    f = f.cut(y_bar(AX, HOOK_Z, 3.3))                               # calibration hook
    return f


def cover():
    c = BODY.intersect(box(-60, 80, -60, 60, Z_BOT - 1, Z_COVER))
    # Nano rides on a central rail (foam tape holds it); the lower header pins hang beside the rail
    c = c.union(box(AX - 5, AX + 5, -21, 21, Z_COVER, PCB_BOT))
    # four side stops keep the board centred (0.4 mm clearance to the board edge)
    for sx in (-1, 1):
        for yy in (-12.0, 12.0):
            x0 = AX + sx * (NANO_W / 2 + 0.4)
            c = c.union(box(min(x0, x0 + sx * 1.4), max(x0, x0 + sx * 1.4), yy - 1.5, yy + 1.5, Z_COVER, PCB_BOT + 1.0))
    # HX711 slides in between two short rails
    for sx in (-1, 1):
        xin = HX_XC + sx * HX_SLOT / 2
        c = c.union(box(min(xin, xin + sx * 1.2), max(xin, xin + sx * 1.2), -5, 5, Z_COVER, Z_COVER + 9.0))
    for bx, by in BOSSES:                                           # two M3 screws, heads in counterbores
        c = c.cut(cyl(M3_CLR / 2, Z_BOT - 2, Z_COVER + 1, cx=bx, cy=by))
        c = c.cut(cyl(3.3, Z_BOT - 1, Z_BOT + 2.2, cx=bx, cy=by))
    return c


def fit_coupon():
    """The palm half from the pod rim up to just past the clamp zone:
    ledge, gusset, boss, and the three bolt holes with counterbores. Stands on its own ring.
    Tests: do all three cell holes line up, does the cell sit flat, does paper slide in the 3 mm gap."""
    return palm(bore=LEGACY_BORE, xl=LEGACY_XL, bay=False).intersect(box(-60, 80, -60, 60, -20, CLAMP + 10))


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
def pocket_plus(z0, z1, wall):
    """The pocket grown by `wall` on every side — if this fits inside the body, the wall is >= `wall` everywhere."""
    g = GAP + wall
    return (cq.Workplane("XY").workplane(offset=z0).center(CT / 2, 0)
            .rect(CT + 2 * g, CW + 2 * g).extrude(z1 - z0).edges("|Z").fillet(g))


if __name__ == "__main__":
    parts = {"palm_half": palm(), "finger_half": finger(), "cover": cover(),
             "fit_coupon": fit_coupon(), "calibration_cradle": cradle()}
    # Only the fit coupon is released now. The three main parts are checked and exported to print_after_G0/:
    # print them once the coupon (G0) has proved the bolt pattern on the real cell.
    RELEASED = {"fit_coupon"}
    AFTER_G0 = {"palm_half", "finger_half", "cover"}
    PR, WIP = os.path.join(OUT, "print_ready"), os.path.join(OUT, "wip")
    AG = os.path.join(OUT, "print_after_G0")
    for d in (PR, WIP, AG):
        os.makedirs(d, exist_ok=True)
    print("part                 valid   size (x y z) mm            volume   ~PETG   status")
    for n, p in parts.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.03, angularTolerance=0.1)
        cq.exporters.export(p, os.path.join(OUT, f"{n}.step"))
        if n in RELEASED:   # every part prints in the orientation it's modelled in (upright), moved to the bed
            cq.exporters.export(to_bed(p), os.path.join(PR, f"{n}_v2_print.stl"), tolerance=0.03, angularTolerance=0.1)
        elif n in AFTER_G0:
            cq.exporters.export(to_bed(p), os.path.join(AG, f"{n}_print_after_G0.stl"), tolerance=0.03, angularTolerance=0.1)
        else:
            cq.exporters.export(to_bed(p), os.path.join(WIP, f"{n}_WIP_do_not_print.stl"),
                                tolerance=0.03, angularTolerance=0.1)
        bb, v = p.val().BoundingBox(), p.val().Volume() / 1000
        print(f"{n:20s} {str(p.val().isValid()):5s}  {bb.xlen:5.0f} x {bb.ylen:4.0f} x {bb.zlen:4.0f}"
              f"   {v:6.1f} cm3   {v*1.27*0.55:4.0f} g   {'READY TO PRINT' if n in RELEASED else ('print after G0' if n in AFTER_G0 else 'WIP - do not print')}")
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

    thin = pocket_plus(0, CL, 2.5).cut(BODY)                         # does pocket + 2.5 mm wall stay inside the body?
    v_thin = thin.val().Volume() if thin.vals() else 0.0

    # every bolt hole in the printed parts must sit on a cell hole (same table drives both, but print it)
    L_BOLT = 25   # one size for both ends

    def bolt_solids(floor_x, sign, zs):
        """Real bolt + washer solids for every hole: washer 12 x 1.6, button head 10.5 x 3.3, M6 x 25 shank."""
        out = None
        for z, y in HOLES_NEAR:
            zz = zs(z)
            parts_ = [bolt_hole(floor_x, floor_x + sign * L_BOLT, y, zz, BOLT) if sign > 0 else
                      bolt_hole(floor_x - L_BOLT, floor_x, y, zz, BOLT),
                      bolt_hole(*sorted((floor_x, floor_x - sign * 1.6)), y, zz, 12.0),
                      bolt_hole(*sorted((floor_x - sign * 1.6, floor_x - sign * 4.9)), y, zz, 10.5)]
            for q in parts_:
                out = q if out is None else out.union(q)
        return out

    pb = bolt_solids(CB_PALM_X, +1, lambda z: z).intersect(parts["palm_half"])
    fb = bolt_solids(CB_FING_X, -1, lambda z: CL - z).intersect(parts["finger_half"])
    v_bolt = (pb.val().Volume() if pb.vals() else 0.0) + (fb.val().Volume() if fb.vals() else 0.0)
    bp = (L_BOLT, L_BOLT - (0 - CB_PALM_X))
    bf = (L_BOLT, L_BOLT - (CB_FING_X - CT))
    assert 1.5 * BOLT <= bp[1] <= CT and 1.5 * BOLT <= bf[1] <= CT, "bolt engagement out of range"
    web = abs(HOLES_NEAR[0][1] - HOLES_NEAR[1][1]) - CBORE_W         # wall between the two pair counterbores
    d_sp = ((HOLES_NEAR[0][0] - HOLES_NEAR[2][0]) ** 2 + (HOLES_NEAR[0][1] - HOLES_NEAR[2][1]) ** 2) ** 0.5 - CBORE_W
    rmax = max(r for r, z in PROFILE if 0 <= z <= CL)
    rmin = min(r for r, z in PROFILE if 0 <= z <= CL)

    # ---- electronics bay checks (P1 / R1) --------------------------------------------------
    def vol(q):
        return q.val().Volume() if q.vals() else 0.0

    pm, fg, cv = parts["palm_half"], parts["finger_half"], parts["cover"]
    nx0, nx1 = AX - NANO_W / 2, AX + NANO_W / 2
    y_pcb = NANO_L / 2
    nano_pcb = box(nx0, nx1, -y_pcb, y_pcb, PCB_BOT, PCB_TOP)
    pins_dn = box(AX - NANO_ROW / 2 - 0.8, AX - NANO_ROW / 2 + 0.8, -19.5, 19.5, PCB_BOT - NANO_PIN, PCB_BOT).union(
        box(AX + NANO_ROW / 2 - 0.8, AX + NANO_ROW / 2 + 0.8, -19.5, 19.5, PCB_BOT - NANO_PIN, PCB_BOT))
    pins_up = box(AX - NANO_ROW / 2 - 0.5, AX - NANO_ROW / 2 + 0.5, -19.5, 19.5, PCB_TOP, PCB_TOP + NANO_PIN).union(
        box(AX + NANO_ROW / 2 - 0.5, AX + NANO_ROW / 2 + 0.5, -19.5, 19.5, PCB_TOP, PCB_TOP + NANO_PIN))
    usb = box(AX - 3.9, AX + 3.9, -y_pcb - 2.0, -y_pcb + 4.0, PCB_TOP, PCB_TOP + NANO_USB_H)
    nano_all = nano_pcb.union(pins_dn).union(pins_up).union(usb)
    plug = box(AX - 5.0, AX + 5.0, -y_pcb - 2.0 - 18.0, -y_pcb - 2.0, USB_ZC - 4.0, USB_ZC + 4.0)   # 10 x 8 plug moulding + 18 mm of cable boot
    hx = box(HX_XC - HX_T / 2, HX_XC + HX_T / 2, -HX_ACROSS / 2, HX_ACROSS / 2, Z_COVER + 9.0 - 6.0 - 0.0, Z_COVER + 9.0 - 6.0 + HX_TALL)
    # (board bottom edge sits on the cover, between the rails; modelled 3 mm into the rail height only for the overlap test)
    hx = box(HX_XC - HX_T / 2, HX_XC + HX_T / 2, -HX_ACROSS / 2, HX_ACROSS / 2, Z_COVER, Z_COVER + HX_TALL)
    wire = cyl(1.5, -18.0, 6.0, cx=EYE[0], cy=EYE[1])                 # 3 mm bundle from the cell exit to the eyelet
    wire_hole = cyl(2.3, -17.5, -8.5, cx=EYE[0], cy=EYE[1])

    e_nano = sum(vol(nano_all.intersect(x)) for x in (pm, cv, fg)) - vol(nano_pcb.intersect(cv))   # pcb touching the rail face is a 0-volume contact
    e_hx = sum(vol(hx.intersect(x)) for x in (pm, fg))
    e_plug = vol(plug.intersect(pm.cut(box(AX - WIN_W/2, AX + WIN_W/2, -40, -18, USB_ZC - WIN_H/2, USB_ZC + WIN_H/2)))) \
        if False else vol(plug.intersect(pm))
    e_wire = vol(wire.intersect(pm)) + vol(wire.intersect(fg)) + vol(wire.intersect(cell()))
    e_cp = vol(cv.intersect(pm)) + vol(cv.intersect(fg))
    e_bosses = vol(cv.intersect(pm))
    bore_wall = cyl(POD_BORE + 2.5, Z_COVER, Z_POD_TOP).cut(BODY)       # bore + 2.5 mm wall stays inside the barrel?
    v_wall = vol(bore_wall)
    win_edge = (Z_COVER - (USB_ZC - WIN_H / 2))                          # window must stay above the cover face (negative = clear)
    nano_corner = (NANO_W / 2) ** 2 + (NANO_L / 2) ** 2
    r_corner = nano_corner ** 0.5
    eye_wall = 26.5 - 25.0                                               # eyelet block penetration into the bore wall
    print(f"""
Electronics bay (P1 round bore, R1 jacket trim + eyelet clamp)
  bore                               diameter {2*POD_BORE:.0f} mm, wall >= 2.5 mm everywhere: {'yes' if v_wall < 0.5 else 'NO (%.1f mm3 outside)' % v_wall}
  Nano corner reach                  {r_corner:.2f} mm from the board centre, bore radius {POD_BORE:.1f} -> {POD_BORE - r_corner:.2f} mm spare at the 4 corners
  Nano stack (z)                     floor {Z_COVER:.1f} | board {PCB_BOT:.1f} .. {PCB_TOP:.1f} | lower pins to {PCB_BOT-NANO_PIN:.1f} | upper pins to {PCB_TOP+NANO_PIN:.1f}
  Nano + pins vs palm/cover/finger   {e_nano:.3f} mm3   (must be 0)
  HX711 (24 tall, 4 thick) vs halves {e_hx:.3f} mm3   (must be 0)
  USB plug + boot vs palm half       {e_plug:.3f} mm3   (must be 0 - plug reaches the connector through the window)
  USB window                         {WIN_W:.0f} wide x {WIN_H:.0f} tall, centre z {USB_ZC:.1f}, connector centre z {USB_ZC:.1f}
  cell wire bundle (3 mm) path       {e_wire:.3f} mm3 vs palm/finger/cell   (must be 0, from cell exit z=+5.6 down to the eyelet)
  cover vs palm / finger half        {e_cp:.3f} mm3   (must be 0)
  eyelet hole {2*2.3:.1f} mm, block fused into the bore wall by {eye_wall:.1f} mm
  cover screws                       M3 x 10, 2 off, diagonal (bosses at {BOSSES}), 10 mm pilots in the bosses
""")
    assert max(e_nano, e_hx, e_plug, e_wire, e_cp) < 0.5, "electronics bay collision"
    assert v_wall < 0.5, "bore wall too thin"
    cpk = (5.0 * CELL_MV_V / 19.53) * 8388608.0 / CELL_CAP_KG

    print(f"""
Checks
  finger half / palm side overlap   {va:.3f} mm3   (must be 0 — the halves never touch)
  load cell / printed parts overlap {vb:.3f} mm3   (must be 0)
  six bolts + washers vs the halves {v_bolt:.3f} mm3   (must be 0 — every bolt passes freely, heads sit in the counterbores)
  load cell bending zone clearance  palm {clr_palm:.2f} mm, finger {clr_fing:.2f} mm  (must be >= {GAP:.0f})
  wall around the pocket (z 0-130)  {'>= 2.5 mm everywhere' if v_thin < 0.5 else f'LESS than 2.5 mm somewhere ({v_thin:.1f} mm3 outside the body)'}
  wall under the finger grooves     {wall_groove:.1f} mm
  grip diameter                     {2*rmin:.1f} - {2*rmax:.1f} mm  (this is the grip span)
  overall height                    {Z_TOP - Z_BOT:.0f} mm

Cell holes (each end, z from that end's face, y across): {[(round(z, 2), round(y, 2)) for z, y in HOLES_NEAR]}
  wall between the two pair counterbores {web:.1f} mm, pair-to-single {d_sp:.1f} mm

Bolts
  palm half    M6 x {bp[0]} button head + washer, 3 off  ({bp[1]:.0f} mm into the cell)
  finger half  M6 x {bf[0]} button head + washer, 3 off  ({bf[1]:.0f} mm into the cell)
  cover        M3 x 10 pan head, 2 off

Expected sensitivity  ~{cpk:,.0f} counts/kg (HX711 gain 128, 5 V, {CELL_MV_V} mV/V, {CELL_CAP_KG:.0f} kg)""")
