"""
dish_base_draft.py — DRAFT: bigger "dish" base that lets the load-cell cable stay UNCUT.

    python dish_base_draft.py        (needs cadquery; run after dynamometer_cad.py is in the same folder)

What changes against the G0-validated design (bolt pattern, clamp, 3 mm gap are untouched):
  * the base is a 112 x 130 mm open tray around the electronics pod (floor + 3 mm rim) — the cable gets room to bend
  * a full-round collar on the palm half rises to z=11, so the cell stays enclosed on every side
  * a round cable port (d 7.6) through the collar wall: 16 mm of STRAIGHT cable from the cell face before any bend
  * finger half starts at z=14 (3 mm above the collar), grooves move up 19 mm
  * the cable is modelled as a swept tube (bend radius 21 mm = ~4 x its diameter) and collision-checked
  * the electronics cover becomes a round plug that sits in the dish floor, flush underneath
  * the R1 eyelet block is gone (no trimming, no eyelet)

v2 (2026-10-14, noon): the first draft read as a phallus (dome on a round shaft on a round flared base). Now: flat chamfered top, rounded-rectangle base.
Everything written here goes to output/draft_dish/ and is marked DO NOT PRINT until Thomas signs the draft off.
"""
import os
import math
import cadquery as cq
import dynamometer_cad as D

D.Z_FINGER_BOT = 14.0                      # finger half starts 3 mm above the collar (z 11)
D.GROOVES_Z = (24.0, 45.0, 66.0, 87.0)     # first groove's lower edge lands on the finger half's lower edge

box, cyl, AX = D.box, D.cyl, D.AX

# ---- v2 silhouette: flat chamfered top (no dome) and a rounded-rectangle base (no round dish)
PROFILE_V2 = D.PROFILE[:11] + [(28.4, 138.0), (28.1, 146.0), (27.2, 150.0)]      # same barrel to z=128, then straight up


def body_flat_top():
    pts = [(AX + r, z) for r, z in PROFILE_V2]
    return (cq.Workplane("XZ").moveTo(AX, D.Z_BOT).lineTo(AX + 30.0, D.Z_BOT).lineTo(*pts[0])
            .spline(pts[1:], includeCurrent=True).lineTo(AX + 24.0, D.Z_TOP).lineTo(AX, D.Z_TOP).close()
            .revolve(360, (AX, 0, 0), (AX, 10, 0)))


D.BODY = body_flat_top()

# ---------------------------------------------------------------- parameters
DISH_HX, DISH_HY, DISH_RC = 56.0, 65.0, 14.0   # base half-width (x), half-length (y), corner radius -> 112 x 130 mm
DISH_WALL = 3.0
DISH_RI = DISH_HY - DISH_WALL            # inner half-length (y), the cable's outer reach is checked against it
DISH_TOP = -2.0                            # rim top
COLLAR_TOP = 11.0                          # palm collar top (finger half starts 3 mm above)
PLUG_R, PLUG_HOLE_R = 26.6, 27.2           # cover plug and the hole it sits in
CABLE_R = D.CABLE_D / 2
CXC = 8.5 + CABLE_R                        # cable centre x  (8.5 mm from the nearest edge, measured)
CZC = 3.0 + CABLE_R                        # cable centre z  (3.0 mm from the end face, measured)
Y_FACE = D.CW / 2                          # cell's +y side face
STRAIGHT = 16.0                            # straight run required before the first bend (>= 15 mm asked for)
R_BEND = 21.0                              # cable centreline bend radius (4.1 x D)
ZE = -40.0                                 # height where the cable enters the pod wall
Y_END = 23.5                               # jacket ends 1.5 mm inside the pod bore (before the Nano rail ends at y=21)
PORT_R = 3.8                               # cable port radius (7.6 mm hole for a 5.13 mm cable)


def y_cyl(r, y0, y1, xc, zc):
    """Cylinder along +y from y0 to y1."""
    return cq.Workplane("XZ").workplane(offset=-y1).center(xc, zc).circle(r).extrude(y1 - y0)


# ---------------------------------------------------------------- parts
def palm_dish():
    p = D.palm(eyelet=False)
    # full-round collar (palm side) so the cell is enclosed up to z=11 on the finger side too
    collar = D.BODY.intersect(box(AX - D.SEAM, 80, -60, 60, D.Z_POD_TOP, COLLAR_TOP)).cut(
        D.pocket(D.Z_POD_TOP - 1, COLLAR_TOP + 1))
    p = p.union(collar)
    # dish: rounded-rectangle rim + floor, with a round hole in the floor for the cover plug
    def rrect(hx, hy, rc, z0, z1):
        return (cq.Workplane("XY").workplane(offset=z0).center(AX, 0).rect(2 * hx, 2 * hy).extrude(z1 - z0)
                .edges("|Z").fillet(rc))
    dish = (rrect(DISH_HX, DISH_HY, DISH_RC, D.Z_BOT, DISH_TOP)
            .cut(rrect(DISH_HX - DISH_WALL, DISH_HY - DISH_WALL, DISH_RC - DISH_WALL, D.Z_COVER, DISH_TOP + 1))
            .cut(cyl(PLUG_HOLE_R, D.Z_BOT - 1, D.Z_COVER)))
    p = p.union(dish)
    # cable port through the collar / palm wall, and the cable entry into the pod wall
    p = p.cut(y_cyl(PORT_R, Y_FACE + 1.0, 45.0, CXC, CZC))
    p = p.cut(y_cyl(PORT_R, 22.0, 34.0, CXC, ZE))
    return p


def finger_dish():
    return D.finger()


def plug():
    """Round cover plug: sits in the floor hole, bottom flush with the dish underside. Same rails/stops as the old cover."""
    c = cyl(PLUG_R, D.Z_BOT, D.Z_COVER)
    c = c.union(box(AX - 5, AX + 5, -21, 21, D.Z_COVER, D.PCB_BOT))
    for sx in (-1, 1):
        for yy in (-12.0, 12.0):
            x0 = AX + sx * (D.NANO_W / 2 + 0.4)
            c = c.union(box(min(x0, x0 + sx * 1.4), max(x0, x0 + sx * 1.4), yy - 1.5, yy + 1.5, D.Z_COVER, D.PCB_BOT + 1.0))
    for sx in (-1, 1):
        xin = D.HX_XC + sx * D.HX_SLOT / 2
        c = c.union(box(min(xin, xin + sx * 1.2), max(xin, xin + sx * 1.2), -5, 5, D.Z_COVER, D.Z_COVER + 9.0))
    for bx, by in D.BOSSES:
        c = c.cut(cyl(D.M3_CLR / 2, D.Z_BOT - 2, D.Z_COVER + 1, cx=bx, cy=by))
        c = c.cut(cyl(3.3, D.Z_BOT - 1, D.Z_BOT + 2.2, cx=bx, cy=by))
    return c


# ---------------------------------------------------------------- cable
def cable_path_pts():
    k = math.sqrt(0.5)
    y1 = Y_FACE + STRAIGHT                       # end of the straight run
    c1 = (y1, CZC - R_BEND)                      # bend 1 centre (turn from +y to -z)
    p2 = (y1 + R_BEND, CZC - R_BEND)
    m1 = (c1[0] + R_BEND * k, c1[1] + R_BEND * k)
    zb = ZE + R_BEND
    c2 = (y1, zb)                                # bend 2 centre (turn from -z to -y)
    p3 = (y1 + R_BEND, zb)
    m2 = (c2[0] + R_BEND * k, c2[1] - R_BEND * k)
    p4 = (y1, ZE)
    return dict(p0=(Y_FACE, CZC), p1=(y1, CZC), m1=m1, p2=p2, p3=p3, m2=m2, p4=p4, p5=(Y_END, ZE))


def cable_tube(extra=0.0):
    q = cable_path_pts()
    path = (cq.Workplane("YZ", origin=(CXC, 0, 0)).moveTo(*q["p0"]).lineTo(*q["p1"])
            .threePointArc(q["m1"], q["p2"]).lineTo(*q["p3"]).threePointArc(q["m2"], q["p4"]).lineTo(*q["p5"]))
    return (cq.Workplane("XZ", origin=(CXC, Y_FACE, CZC)).circle(CABLE_R + extra).sweep(path))


def cable_length():
    q = cable_path_pts()
    arc = math.pi / 2 * R_BEND
    return (q["p1"][0] - q["p0"][0]) + arc + (q["p2"][1] - q["p3"][1]) + arc + (q["p4"][0] - q["p5"][0])


def vol(q):
    return q.val().Volume() if q.vals() else 0.0


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    OUT = os.path.join(D.OUT, "draft_dish")
    os.makedirs(OUT, exist_ok=True)
    parts = {"palm_dish": palm_dish(), "finger_dish": finger_dish(), "plug": plug()}
    for n, p in parts.items():
        cq.exporters.export(D.to_bed(p), os.path.join(OUT, f"{n}_v2_DRAFT_do_not_print.stl"), tolerance=0.03, angularTolerance=0.1)
        cq.exporters.export(p, os.path.join(OUT, f"{n}_v2_DRAFT.step"))
    cq.exporters.export(cable_tube(), os.path.join(OUT, "cable_path_model_v2.stl"), tolerance=0.03, angularTolerance=0.1)

    pm, fg, pl, cell = parts["palm_dish"], parts["finger_dish"], parts["plug"], D.cell()
    print("part          valid   size (x y z) mm            volume")
    for n, p in parts.items():
        bb = p.val().BoundingBox()
        print(f"{n:12s}  {str(p.val().isValid()):5s}  {bb.xlen:5.0f} x {bb.ylen:4.0f} x {bb.zlen:4.0f}   {p.val().Volume()/1000:6.1f} cm3")

    # --- the halves never touch
    ov = {"palm/finger": vol(pm.intersect(fg)), "palm/plug": vol(pm.intersect(pl)), "finger/plug": vol(fg.intersect(pl)),
          "cell/palm": vol(cell.intersect(pm)), "cell/finger": vol(cell.intersect(fg)), "cell/plug": vol(cell.intersect(pl))}
    print("\nOverlaps (mm3, must be 0):", {k: round(v, 3) for k, v in ov.items()})

    # --- cable clearance: grow the cable tube until it hits something
    print("\nCable clearance (tube grown by c mm; volume = overlap with palm+finger+plug, 0 = clear)")
    clear = 0.0
    for c in (0.0, 0.5, 1.0, 1.2, 1.5, 2.0):
        t = cable_tube(c)
        v = vol(t.intersect(pm)) + vol(t.intersect(fg)) + vol(t.intersect(pl))
        print(f"  +{c:.1f} mm  -> {v:8.2f} mm3  {'clear' if v < 0.5 else 'HITS'}")
        if v < 0.5:
            clear = c
    q = cable_path_pts()
    print(f"\nStraight run from the cell face       {q['p1'][0]-q['p0'][0]:.1f} mm   (asked >= 15)")
    print(f"Bend radius (centreline)              {R_BEND:.1f} mm = {R_BEND/D.CABLE_D:.1f} x cable diameter")
    print(f"Cable length used by this path        {cable_length():.0f} mm  (cell face -> 1.5 mm inside the pod); the rest of the cable coils in the dish")
    print(f"Clear all round the cable             {clear:.1f} mm (largest clearance tested)")
    print(f"Outermost cable reach                 y = {q['p2'][0]+CABLE_R:.1f} mm vs rim inner wall {DISH_RI:.1f} mm")
    print(f"Top of the handle                     flat, z = {D.Z_TOP:.1f}; hook hole top edge z = {D.HOOK_Z + 3.3:.1f} (material above it {D.Z_TOP - D.HOOK_Z - 3.3:.1f} mm)")

    # --- spare-cable capacity (coils lying around the pod, centreline radius >= 33 mm so every turn is >= R21)
    r0, r1 = 30.0 + 1.0 + CABLE_R, (DISH_HX - DISH_WALL) - 1.0 - CABLE_R   # round loops, limited by the narrow x side
    pitch = D.CABLE_D + 0.5
    n_rad = int((r1 - r0) / pitch) + 1
    n_lay = int(((DISH_TOP - 3.0) - ZE) / pitch) + 1
    turns = [2 * math.pi * (r0 + i * pitch) for i in range(n_rad)]
    cap = sum(turns) * n_lay
    print(f"Spare-cable room                      {n_rad} radial x {n_lay} layers -> {cap/1000:.1f} m of cable at 100% packing, ~{cap*0.4/1000:.1f} m at a realistic 40%")

    # --- wall checks
    print(f"Dish rim {DISH_WALL:.1f} mm thick, floor {abs(D.Z_COVER - D.Z_BOT):.0f} mm thick, overall palm height {pm.val().BoundingBox().zlen:.0f} mm")
    print(f"Finger half starts z={D.Z_FINGER_BOT:.0f} ({D.Z_FINGER_BOT-COLLAR_TOP:.0f} mm above the collar); cable top at z={CZC+CABLE_R:.1f}")
