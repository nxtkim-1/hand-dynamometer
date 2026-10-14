"""
compact_base_draft.py — DRAFT v3 "compact box": the uncut load-cell cable lives inside a closed base.

    python compact_base_draft.py        (needs cadquery; dynamometer_cad.py must be in the same folder)

Why: the cable leaves the cell's side face 3 mm above the cell's bottom, it will not be cut,
and it needs at least 15 mm of free space beside the cell before it can turn (Thomas, 2026-10-14).

What changes against the G0-validated design (bolt pattern, clamp, ledge, 3 mm gap are untouched):
  * the palm half's base becomes a closed rounded box, 57 x 82 mm, top at z = 12 (just above the cable exit)
  * inside the box the cable has 18.5 mm from the cell face to the end wall, turns down at R 11,
    and the spare length coils around the box floor (one or two loops wide, up to 4 layers)
  * the cable touches only the palm half (the box). It never reaches the finger half or the
    moving part of the cell, so it cannot carry any of the squeeze force
  * finger half starts at z = 15 (3 mm above the box top); finger grooves move up 20 mm
  * the Nano lies along x on the floor with its USB through the palm-side wall; the HX711 sits
    on a small shelf on the -y end wall, above the Nano
  * flat chamfered top (no dome), same as the dish v2 draft
  * a cable slot in the box top lets the cell, with its cable already bent, be lowered in from above

Everything goes to output/draft_compact/ and is marked DO NOT PRINT until Thomas approves the draft.
"""
import os
import math
import cadquery as cq
import dynamometer_cad as D

box, cyl, AX = D.box, D.cyl, D.AX

# ---------------------------------------------------------------- silhouette: flat chamfered top (as dish v2)
PROFILE_V2 = D.PROFILE[:11] + [(28.4, 138.0), (28.1, 146.0), (27.2, 150.0)]


def body_flat_top():
    pts = [(AX + r, z) for r, z in PROFILE_V2]
    return (cq.Workplane("XZ").moveTo(AX, D.Z_BOT).lineTo(AX + 30.0, D.Z_BOT).lineTo(*pts[0])
            .spline(pts[1:], includeCurrent=True).lineTo(AX + 24.0, D.Z_TOP).lineTo(AX, D.Z_TOP).close()
            .revolve(360, (AX, 0, 0), (AX, 10, 0)))


D.BODY = body_flat_top()

# ---------------------------------------------------------------- box
BOX_TOP = 12.0                    # top of the box (cable top is at z = 8.1)
TOP_WALL, WALL = 2.5, 2.5
Z_CEIL = BOX_TOP - TOP_WALL       # 9.5, inside ceiling
BOX_HX = 28.5                     # half-width in x about the grip axis: same as the grip, so no ledge under the palm
BOX_HY = 41.0                     # half-length in y: inner wall at 38.5 -> 18.5 mm from the cell's side face
BOX_RC = 12.0                     # corner radius (outside)
Z_BOX_BOT = -52.0
COVER_T = 3.5
Z_FLOOR = Z_BOX_BOT + COVER_T     # -48.5, top face of the cover = floor of the box
D.Z_FINGER_BOT = BOX_TOP + 3.0    # 15
D.GROOVES_Z = (25.0, 46.0, 67.0, 88.0)   # lowest groove's lower edge sits on the finger half's lower edge

IN_HX, IN_HY = BOX_HX - WALL, BOX_HY - WALL          # 26.0, 38.5
X_IN0, X_IN1 = AX - IN_HX, AX + IN_HX                # -15.0, 37.0

# ---------------------------------------------------------------- cable (measured 2026-10-12/14)
CABLE_R = D.CABLE_D / 2
CXC = 8.5 + CABLE_R               # centre x: 8.5 mm from the nearest edge of the 22 mm face
CZC = 3.0 + CABLE_R               # centre z: 3.0 mm above the cell's end face
Y_FACE = D.CW / 2                 # the cell's +y side face
STRAIGHT = 3.5                    # straight run out of the cell before the bend
R_BEND = 11.0                     # bend radius at the cable centreline (2.1 x cable diameter)

# ---------------------------------------------------------------- spare-cable coil zone (around the floor)
PITCH = D.CABLE_D + 0.5           # one cable width with a little slack
COIL_RINGS = 2                    # two loops side by side
COIL_RC = 20.0                    # corner radius of the outer loop (outer edge) -> centreline 17.4, inner loop 11.8
COIL_TOP = -23.0                  # under the ledge gusset

# ---------------------------------------------------------------- electronics
NANO_L, NANO_W, PCB_T = D.NANO_L, D.NANO_W, D.PCB_T
NANO_XL = X_IN0 + 1.0 + 2.0       # PCB end on the USB side: connector face 1 mm inside the -x wall
RAIL_H = D.NANO_PIN + 1.5
PCB_BOT = Z_FLOOR + RAIL_H
PCB_TOP = PCB_BOT + PCB_T
USB_ZC = PCB_TOP + D.NANO_USB_H / 2
WIN_W, WIN_H = 14.0, 11.0         # USB window (plug moulding not measured yet; ~10 x 8 assumed)
HX_L, HX_H, HX_T = 24.0, 16.0, 4.0                      # HX711, board plane parallel to the -y wall
HX_X0 = AX - HX_L / 2
HX_Z0 = -14.0                     # bottom edge of the HX711 (sits on a shelf)
HX_Y0 = -IN_HY                    # back of the board against the wall

# cover screws: four M3, bosses tucked into the corners outside the coil
BOSS_R = 3.4
BOSS_H = 14.0
BOSSES = [(X_IN0 + 3.2, IN_HY - 3.2), (X_IN1 - 3.2, IN_HY - 3.2),
          (X_IN0 + 3.2, -IN_HY + 3.2), (X_IN1 - 3.2, -IN_HY + 3.2)]
# Nano: board edge 0.5 mm clear of the two -y corner bosses (it spans almost the whole inside width)
NANO_YC = -IN_HY + 3.2 + BOSS_R + 0.5 + NANO_W / 2
COIL_Y0 = NANO_YC + NANO_W / 2 + 0.4 + 1.4 + 0.5          # spare-cable loops start just past the Nano's side stops

OUT = os.path.join(D.OUT, "draft_compact")


def rrect(hx, hy, rc, z0, z1, cx=AX, cy=0.0):
    return (cq.Workplane("XY").workplane(offset=z0).center(cx, cy).rect(2 * hx, 2 * hy)
            .extrude(z1 - z0).edges("|Z").fillet(rc))


def outer(z0, z1):
    return rrect(BOX_HX, BOX_HY, BOX_RC, z0, z1)


def inner(z0, z1):
    return rrect(IN_HX, IN_HY, BOX_RC - WALL, z0, z1)


# ---------------------------------------------------------------- parts
def palm_compact():
    grip = D.BODY.intersect(box(-60, AX - D.SEAM, -60, 60, BOX_TOP, D.Z_PALM_TOP)).cut(
        D.pocket(BOX_TOP - 1, D.Z_PALM_TOP + 1))
    shell = outer(Z_FLOOR, BOX_TOP).cut(inner(Z_FLOOR - 1, Z_CEIL)).cut(D.pocket(Z_CEIL - 1, BOX_TOP + 1))
    p = grip.union(shell)
    # clamp boss, ledge and 45 deg gusset — as validated by the fit coupon, now fused into the -x wall
    xl = X_IN0 - 1.0
    feat = box(xl, 0, -D.BY, D.BY, 0, D.CLAMP)
    feat = feat.union(box(xl, 5, -D.BY, D.BY, -3, 0))
    feat = feat.union(D.wedge_xz([(xl, -3), (5, -3), (xl, -3 + (xl - 5))], -D.BY, D.BY))
    p = p.union(feat.intersect(D.BODY.union(outer(Z_FLOOR, BOX_TOP))))
    for z, y in D.HOLES_NEAR:
        p = p.cut(D.bolt_hole(-60, 1, y, z, D.HOLE_CLR))
        p = p.cut(D.bolt_hole(-60, D.CB_PALM_X, y, z, D.CBORE_W))
    # cover screw bosses, fused into the corners
    for bx, by in BOSSES:
        p = p.union(cyl(BOSS_R, Z_FLOOR, Z_FLOOR + BOSS_H, cx=bx, cy=by).intersect(outer(Z_FLOOR, BOX_TOP)))
        p = p.cut(cyl(D.M3_PILOT / 2, Z_FLOOR - 1, Z_FLOOR + 10, cx=bx, cy=by))
    # HX711 shelf on the -y end wall (board sits on it, foam tape to the wall); 45 deg underside prints without support
    d = HX_T + 1.0
    shelf = (cq.Workplane("YZ").polyline([(-IN_HY - 0.5, HX_Z0), (-IN_HY + d, HX_Z0), (-IN_HY + d, HX_Z0 - 1.5),
                                          (-IN_HY - 0.5, HX_Z0 - 1.5 - (d + 0.5))]).close()
             .extrude(HX_L - 4).translate((HX_X0 + 2, 0, 0)))
    p = p.union(shelf)
    # USB window through the palm-side (-x) wall
    p = p.cut(box(AX - BOX_HX - 2, X_IN0 + 1, NANO_YC - WIN_W / 2, NANO_YC + WIN_W / 2,
                  USB_ZC - WIN_H / 2, USB_ZC + WIN_H / 2))
    # cable slot through the box top: lets the cell (cable already bent) be lowered in from above
    p = p.cut(box(CXC - 3.5, CXC + 3.5, Y_FACE + D.GAP - 0.5, IN_HY, Z_CEIL - 1, BOX_TOP + 1))
    return p


def finger_compact():
    return D.finger()


def base_test():
    """Cheap test print: the palm half's box plus the clamp zone, nothing above it. With the real cell bolted on,
    it tests the cable bay and coil room, the Nano/HX711/USB fit and the cover screws before the full parts are printed."""
    return palm_compact().intersect(box(-60, 80, -60, 60, Z_BOX_BOT - 1, D.CLAMP + 6))


def cover_compact():
    c = outer(Z_BOX_BOT, Z_FLOOR)
    # Nano rail along x (foam tape on top); the lower header pins hang either side of it
    c = c.union(box(NANO_XL + 1, NANO_XL + NANO_L - 1, NANO_YC - 5, NANO_YC + 5, Z_FLOOR, PCB_BOT))
    for sy in (-1, 1):
        y0 = NANO_YC + sy * (NANO_W / 2 + 0.4)
        for xx in (NANO_XL + 10, NANO_XL + NANO_L - 10):
            c = c.union(box(xx - 1.5, xx + 1.5, min(y0, y0 + sy * 1.4), max(y0, y0 + sy * 1.4), Z_FLOOR, PCB_BOT + 1.0))
    for bx, by in BOSSES:
        c = c.cut(cyl(D.M3_CLR / 2, Z_BOX_BOT - 1, Z_FLOOR + 1, cx=bx, cy=by))
        c = c.cut(cyl(3.0, Z_BOX_BOT - 1, Z_BOX_BOT + 1.8, cx=bx, cy=by))     # pan head sits flush
    return c


# ---------------------------------------------------------------- cable and envelopes (for the checks)
def cable_pts():
    y1 = Y_FACE + STRAIGHT
    k = math.sqrt(0.5)
    c1 = (y1, CZC - R_BEND)
    return dict(p0=(Y_FACE, CZC), p1=(y1, CZC), m=(c1[0] + R_BEND * k, c1[1] + R_BEND * k),
                p2=(y1 + R_BEND, CZC - R_BEND), p3=(y1 + R_BEND, COIL_TOP))


def cable_tube(extra=0.0):
    q = cable_pts()
    path = (cq.Workplane("YZ", origin=(CXC, 0, 0)).moveTo(*q["p0"]).lineTo(*q["p1"])
            .threePointArc(q["m"], q["p2"]).lineTo(*q["p3"]))
    return cq.Workplane("XZ", origin=(CXC, Y_FACE, CZC)).circle(CABLE_R + extra).sweep(path)


def coil_geom():
    x0, x1 = X_IN0 + 0.5, X_IN1 - 0.5
    y0, y1 = COIL_Y0, IN_HY - 0.5
    return (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2


def coil_zone():
    cx, cy, hx, hy = coil_geom()
    w = COIL_RINGS * PITCH
    return (rrect(hx, hy, COIL_RC, Z_FLOOR, COIL_TOP, cx, cy)
            .cut(rrect(hx - w, hy - w, COIL_RC - w, Z_FLOOR - 1, COIL_TOP + 1, cx, cy)))


def coil_capacity():
    cx, cy, hx, hy = coil_geom()
    layers = int((COIL_TOP - Z_FLOOR) // PITCH)
    per_ring = []
    for i in range(COIL_RINGS):
        off = CABLE_R + 0.25 + i * PITCH                  # centreline of loop i
        a, b, r = hx - off, hy - off, COIL_RC - off
        per_ring.append((2 * (2 * a + 2 * b) - (8 - 2 * math.pi) * r, r))
    return layers, per_ring


def nano_env():
    pcb = box(NANO_XL, NANO_XL + NANO_L, NANO_YC - NANO_W / 2, NANO_YC + NANO_W / 2, PCB_BOT, PCB_TOP)
    rows = None
    for s in (-1, 1):
        yy = NANO_YC + s * D.NANO_ROW / 2
        r = box(NANO_XL + 2.5, NANO_XL + NANO_L - 2.5, yy - 0.8, yy + 0.8, PCB_BOT - D.NANO_PIN, PCB_BOT).union(
            box(NANO_XL + 2.5, NANO_XL + NANO_L - 2.5, yy - 0.5, yy + 0.5, PCB_TOP, PCB_TOP + D.NANO_PIN))
        rows = r if rows is None else rows.union(r)
    usb = box(NANO_XL - 2.0, NANO_XL + 4.0, NANO_YC - 3.9, NANO_YC + 3.9, PCB_TOP, PCB_TOP + D.NANO_USB_H)
    return pcb, rows.union(usb)


def plug_env():
    """mini-B plug moulding (10 x 8, assumed) starting at the connector face, plus 18 mm of cable boot."""
    return box(NANO_XL - 2.0 - 18.0, NANO_XL - 2.0, NANO_YC - 5.0, NANO_YC + 5.0, USB_ZC - 4.0, USB_ZC + 4.0)


def hx_env():
    return box(HX_X0, HX_X0 + HX_L, HX_Y0, HX_Y0 + HX_T, HX_Z0, HX_Z0 + HX_H)


def vol(q):
    try:
        return q.val().Volume() if q.vals() else 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pm, fg, cv, cell = palm_compact(), finger_compact(), cover_compact(), D.cell()
    parts = {"palm_compact": pm, "finger_compact": fg, "cover_compact": cv, "base_test": base_test()}
    print("part              valid   size (x y z) mm          volume   ~PETG (55% fill)")
    for n, p in parts.items():
        cq.exporters.export(D.to_bed(p), os.path.join(OUT, f"{n}_v3_DRAFT_do_not_print.stl"), tolerance=0.03, angularTolerance=0.1)
        cq.exporters.export(p, os.path.join(OUT, f"{n}_v3_DRAFT.step"))
        bb, v = p.val().BoundingBox(), p.val().Volume() / 1000
        print(f"{n:16s}  {str(p.val().isValid()):5s}  {bb.xlen:5.1f} x {bb.ylen:5.1f} x {bb.zlen:5.1f}   {v:6.1f} cm3   {v*1.27*0.55:4.0f} g")
    cq.exporters.export(cable_tube(), os.path.join(OUT, "cable_path_v3.stl"), tolerance=0.03, angularTolerance=0.1)
    cq.exporters.export(coil_zone(), os.path.join(OUT, "coil_zone_v3.stl"), tolerance=0.05, angularTolerance=0.2)

    # 1. the force path: halves never touch, nothing touches the cell's bending zone
    ov = {"palm/finger": vol(pm.intersect(fg)), "cover/finger": vol(cv.intersect(fg)), "cover/palm": vol(cv.intersect(pm)),
          "cell/palm": vol(cell.intersect(pm)), "cell/finger": vol(cell.intersect(fg)), "cell/cover": vol(cell.intersect(cv))}
    gap_pf = pm.val().distance(fg.val())
    flex = box(0, D.CT, -D.CW / 2, D.CW / 2, D.CLAMP + 5, D.CL - D.CLAMP - 5)
    clr_palm, clr_fing = flex.val().distance(pm.val()), flex.val().distance(fg.val())
    print("\nForce path")
    print("  overlaps (mm3, all must be 0):", {k: round(v, 3) for k, v in ov.items()})
    print(f"  smallest gap palm half <-> finger half   {gap_pf:.2f} mm   (must be >= 3)")
    print(f"  bending-zone clearance  palm {clr_palm:.2f} mm, finger {clr_fing:.2f} mm   (must be >= 3)")

    # 2. the cable
    tube = cable_tube()
    hit_cell_flex = vol(tube.intersect(box(0, D.CT, -D.CW / 2, D.CW / 2, D.BLOCK, D.CL)))
    v_tube_parts = vol(tube.intersect(pm)) + vol(tube.intersect(fg)) + vol(tube.intersect(cv))
    clear = 0.0
    for c in (0.5, 1.0, 1.3):
        t = cable_tube(c)
        if vol(t.intersect(pm)) + vol(t.intersect(fg)) + vol(t.intersect(cv)) < 0.05:
            clear = c
    d_fing = tube.val().distance(fg.val())
    q = cable_pts()
    reach = q["p2"][0] + CABLE_R
    print("\nCable")
    print(f"  space from the cell's side face to the end wall   {IN_HY - Y_FACE:.1f} mm   (asked >= 15)")
    print(f"  path: {STRAIGHT:.1f} mm straight, then a {R_BEND:.0f} mm bend ({R_BEND / D.CABLE_D:.1f} x diameter); outer edge reaches y = {reach:.1f} (wall {IN_HY:.1f})")
    print(f"  cable vs printed parts   {v_tube_parts:.3f} mm3 (must be 0); clear all round by at least {clear:.1f} mm")
    print(f"  cable vs the finger half  {d_fing:.2f} mm away  (it must never touch: that would shunt force)")
    print(f"  cable top z = {CZC + CABLE_R:.1f}, box ceiling z = {Z_CEIL:.1f}; cable slot in the box top {7.0:.0f} mm wide")

    # 3. spare-cable storage
    cz = coil_zone()
    pcb, nano_rest = nano_env()
    hx, plug = hx_env(), plug_env()
    v_coil = {"palm": vol(cz.intersect(pm)), "cover": vol(cz.intersect(cv)), "Nano": vol(cz.intersect(pcb.union(nano_rest))),
              "HX711": vol(cz.intersect(hx)), "USB plug": vol(cz.intersect(plug))}
    layers, rings = coil_capacity()
    print("\nSpare-cable coil zone (two loops wide around the floor)")
    print("  overlaps (mm3, all must be 0):", {k: round(v, 3) for k, v in v_coil.items()})
    tot = 0.0
    for i, (L, r) in enumerate(rings):
        tot += L * layers
        print(f"  loop {i + 1}: {L:.0f} mm per turn, tightest bend {r:.1f} mm, {layers} layers -> {L * layers:.0f} mm")
    print(f"  total room for spare cable about {tot:.0f} mm (coil zone z {Z_FLOOR:.1f} .. {COIL_TOP:.1f})")

    # 4. electronics
    e_nano = vol(pcb.intersect(pm)) + vol(pcb.intersect(fg)) + vol(nano_rest.intersect(pm)) + vol(nano_rest.intersect(cv)) + vol(nano_rest.intersect(fg))
    e_hx = vol(hx.intersect(pm)) + vol(hx.intersect(cv)) + vol(hx.intersect(fg)) + vol(hx.intersect(pcb.union(nano_rest)))
    e_plug = vol(plug.intersect(pm)) + vol(plug.intersect(cv))
    print("\nElectronics")
    print(f"  Nano + pins + USB connector vs parts   {e_nano:.3f} mm3 (must be 0)")
    print(f"  HX711 (24 x 16 x 4, nominal) vs parts  {e_hx:.3f} mm3 (must be 0)")
    print(f"  USB plug through the palm-side window  {e_plug:.3f} mm3 (must be 0; window {WIN_W:.0f} x {WIN_H:.0f}, centre z {USB_ZC:.1f})")
    print(f"  room above the Nano's pin tips         {HX_Z0 - (PCB_TOP + D.NANO_PIN):.1f} mm up to the HX711 (enough for Dupont plugs on the bench)")

    # 5. walls and bolts
    thin = D.pocket_plus(BOX_TOP, D.CL, 2.5).cut(D.BODY)
    print("\nWalls and bolts")
    print(f"  grip wall around the cell (z {BOX_TOP:.0f}..130) {'>= 2.5 mm everywhere' if vol(thin) < 0.5 else 'THIN somewhere'}")
    for L in (20, 25):
        e = L - 1.6 - (0 - D.CB_PALM_X)
        print(f"  M6 x {L} + washer: {e:.1f} mm of thread in the cell ({e / D.BOLT:.1f} x D)")
    bb = pm.val().BoundingBox()
    print(f"\nSize: box {2 * BOX_HX:.0f} x {2 * BOX_HY:.0f} mm, overall height {D.Z_TOP - Z_BOX_BOT:.0f} mm; "
          f"finger half from z = {D.Z_FINGER_BOT:.0f}, grooves at {D.GROOVES_Z}")
