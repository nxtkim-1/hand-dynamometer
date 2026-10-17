"""
jamar_concept.py — CONCEPT ONLY (2026-10-16): a Jamar / Camry-style two-handle dynamometer built
around the same load cell, bolts and electronics. Not checked for printing; not released.

    python jamar_concept.py          (needs cadquery; dynamometer_cad.py in the same folder)

Layout (x = squeeze direction, z = up, hand goes in from the side):

    palm bar | window for the hand | finger bar | fingertip gap | BODY (cell + electronics)
       ^ frame (fixed side) ^                ^ finger part ^       ^ frame ^

  * FRAME (grey): a box-shaped body holding the load cell upright, plus a top arm and a bottom arm
    that reach out to the palm bar. The cell's lower (cable) end bolts to the back of the body.
  * PALM BAR (grey, separate): bolts between the two arms at one of 5 positions -> adjustable grip span,
    like a Jamar's 5 handle positions. It sits on the fixed side, so moving it never touches the force path.
  * FINGER PART (black): a bracket bolted to the cell's upper (free) end, reaching out through an
    opening in the body, with the finger bar hanging down from it.
  * The only path from finger part to frame is through the load cell. 3 mm gaps everywhere else.

Same rules as the split-grip design: 3 mm gaps, cable stays on the fixed side, 18.5 mm cable bay,
the G0-tested 3-hole bolt pattern at both ends.
"""
import os
import math
import cadquery as cq
import dynamometer_cad as D

box, cyl = D.box, D.cyl
G = 3.0                                   # gap between moving and fixed parts
T = 3.0                                   # body wall

# ---------------------------------------------------------------- finger part (moving)
FB_X0, FB_X1 = -50.0, -26.0               # finger bar, 24 deep in x
FB_Y = 18.0                               # finger bar half-width (36 wide)
FB_Z0 = 33.0                              # bottom of the finger bar
BR_Z0, BR_Z1 = 97.0, 133.0                # bracket on the cell's free end block (z 97..130)
BR_Y = 17.0

# ---------------------------------------------------------------- frame (fixed)
BX0, BX1 = FB_X1 + 20.0, 39.0             # body x: fingertip gap 20 mm behind the finger bar; back wall
BY = 41.0                                 # body half-width: inner wall 38 -> 18 mm cable bay beside the cell
BZ0 = -50.0                               # body bottom (cover below)
ROOF0, ROOF1 = BR_Z1 + G, BR_Z1 + G + 12.0          # top arm / roof, z 136..148
ARM_LO0, ARM_LO1 = FB_Z0 - G - 12.0, FB_Z0 - G      # bottom arm, z 18..30
ARM_Y = 20.0                              # arms 40 wide
PB_T, PB_Y = 20.0, 18.0                   # palm bar 20 deep, 36 wide
GAPS = (26.0, 36.0, 46.0, 56.0, 66.0)     # palm bar to finger bar, 5 positions (placeholders until a real Jamar is measured)
POS = 1                                   # drawn at position 2
ARM_X0 = FB_X0 - GAPS[-1] - PB_T - 6.0    # arms reach the farthest position
COVER_T = 3.0


def rbox(x0, x1, y0, y1, z0, z1, r):
    return box(x0, x1, y0, y1, z0, z1).edges("|Z").fillet(r)


def frame():
    body = rbox(BX0, BX1, -BY, BY, BZ0, ROOF1, 8.0)
    cav = rbox(BX0 + T, BX1 - T, -BY + T, BY - T, BZ0 - 1, ROOF0, 5.0)
    f = body.cut(cav)
    f = f.cut(box(BX0 - 1, BX0 + T + 1, -BR_Y - G, BR_Y + G, BR_Z0 - G, BR_Z1 + G))      # opening for the bracket
    f = f.union(box(ARM_X0, BX0 + 1, -ARM_Y, ARM_Y, ROOF0, ROOF1))                       # top arm
    f = f.union(box(ARM_X0, BX0 + 1, -ARM_Y, ARM_Y, ARM_LO0, ARM_LO1))                   # bottom arm
    # fixed-end clamp on the BACK of the cell (+x), same hole pattern as G0, ledge + 45 deg gusset under it
    xb = BX1 - T + 1.0
    f = f.union(box(D.CT, xb, -D.BY, D.BY, 0, D.CLAMP))
    f = f.union(box(D.CT - 7, xb, -D.BY, D.BY, -3, 0))
    f = f.union(D.wedge_xz([(D.CT - 7, -3), (xb, -3), (xb, -3 - (xb - D.CT + 7))], -D.BY, D.BY))
    for z, y in D.HOLES_NEAR:
        f = f.cut(D.bolt_hole(D.CT - 1, BX1 + 5, y, z, D.HOLE_CLR))
        f = f.cut(D.bolt_hole(D.CB_FING_X, BX1 + 5, y, z, D.CBORE_W))
    # palm-bar holes: one vertical M5 hole per position in each arm
    for g in GAPS:
        xc = FB_X0 - g - PB_T / 2
        f = f.cut(cyl(2.7, ARM_LO0 - 1, ARM_LO1 + 1, cx=xc, cy=0)).cut(cyl(2.7, ROOF0 - 1, ROOF1 + 1, cx=xc, cy=0))
    return f


def palm_bar(pos=POS):
    g = GAPS[pos]
    x1 = FB_X0 - g
    b = rbox(x1 - PB_T, x1, -PB_Y, PB_Y, ARM_LO1, ROOF0, 6.0)
    return b.cut(cyl(2.2, ARM_LO1 - 1, ARM_LO1 + 15, cx=x1 - PB_T / 2, cy=0)).cut(cyl(2.2, ROOF0 - 15, ROOF0 + 1, cx=x1 - PB_T / 2, cy=0))


def finger():
    f = box(FB_X0, 0, -BR_Y, BR_Y, BR_Z0, BR_Z1)                          # bracket on the cell's free end (-x face)
    f = f.union(rbox(FB_X0, FB_X1, -FB_Y, FB_Y, FB_Z0, BR_Z0 + 5, 5.0))   # finger bar
    for z, y in D.HOLES_NEAR:
        zz = D.CL - z
        f = f.cut(D.bolt_hole(FB_X0 - 5, 1, y, zz, D.HOLE_CLR))
        f = f.cut(D.bolt_hole(FB_X0 - 5, -11.0, y, zz, D.CBORE_W))         # long counterbore: head seats at x = -11
    return f


def cover():
    return rbox(BX0, BX1, -BY, BY, BZ0 - COVER_T, BZ0, 8.0)


def cable_tube():
    r = D.CABLE_D / 2
    xc, zc, y0 = 8.5 + r, 3.0 + r, D.CW / 2
    y1, R = y0 + 3.5, 11.0
    k = math.sqrt(0.5)
    path = (cq.Workplane("YZ", origin=(xc, 0, 0)).moveTo(y0, zc).lineTo(y1, zc)
            .threePointArc((y1 + R * k, zc - R + R * k), (y1 + R, zc - R)).lineTo(y1 + R, -30))
    return cq.Workplane("XZ", origin=(xc, y0, zc)).circle(r).sweep(path)


def electronics_zone():
    return box(BX0 + T + 1, BX1 - T - 1, -BY + T + 1, BY - T - 1, BZ0 + 1, -25)


def vol(q):
    try:
        return q.val().Volume() if q.vals() else 0.0
    except Exception:
        return 0.0


if __name__ == "__main__":
    OUT = os.path.join(D.OUT, "concept_jamar")
    os.makedirs(OUT, exist_ok=True)
    fr, pb, fg, cv, cell = frame(), palm_bar(), finger(), cover(), D.cell()
    fixed = fr.union(pb).union(cv)
    for n, p in {"frame": fr, "palm_bar": pb, "finger_part": fg, "cover": cv}.items():
        cq.exporters.export(p, os.path.join(OUT, f"{n}_CONCEPT.step"))
        bb = p.val().BoundingBox()
        print(f"{n:12s} valid {p.val().isValid()}  {bb.xlen:5.0f} x {bb.ylen:4.0f} x {bb.zlen:4.0f} mm  {p.val().Volume()/1000:6.1f} cm3")
    print("\nForce path")
    print(f"  finger part vs fixed parts overlap  {vol(fg.intersect(fixed)):.3f} mm3 (must be 0)")
    print(f"  smallest gap finger part <-> frame  {fg.val().distance(fr.val()):.2f} mm, <-> palm bar {fg.val().distance(pb.val()):.2f} mm (>= 3)")
    flex = box(0, D.CT, -D.CW / 2, D.CW / 2, D.CLAMP + 5, D.CL - D.CLAMP - 5)
    print(f"  cell bending zone to frame {flex.val().distance(fr.val()):.2f} mm, to finger part {flex.val().distance(fg.val()):.2f} mm (>= 3)")
    print(f"  cell vs parts overlap {vol(cell.intersect(fixed)) + vol(cell.intersect(fg)):.3f} mm3 (must be 0)")
    ct = cable_tube()
    print(f"  cable vs parts {vol(ct.intersect(fixed)) + vol(ct.intersect(fg)):.3f} mm3 (must be 0); cable to finger part {ct.val().distance(fg.val()):.1f} mm")
    print(f"  palm bar position check, all 5: {[round(fg.val().distance(palm_bar(i).val()), 1) for i in range(5)]} mm")
    print("\nHand")
    for i, g in enumerate(GAPS):
        print(f"  position {i+1}: bar-to-bar gap {g:.0f} mm, outer span (palm face to finger face) {g + PB_T + FB_X1 - FB_X0:.0f} mm")
    print(f"  window height (arm to arm) {ROOF0 - ARM_LO1:.0f} mm; finger surface (bar + bracket front) z {FB_Z0:.0f}..{BR_Z1:.0f} = {BR_Z1 - FB_Z0:.0f} mm")
    print(f"  fingertip gap behind the finger bar {BX0 - FB_X1:.0f} mm")
    bb = fixed.union(fg).val().BoundingBox()
    print(f"\nOverall {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm")
    # rough stress at 100 kg (981 N), finger bar root and bracket bolts
    F = 981.0
    zf = (FB_Z0 + BR_Z0) / 2
    M_bar = F * (BR_Z0 - zf)
    Zs = (2 * FB_Y) * (FB_X1 - FB_X0) ** 2 / 6
    print(f"\nAt 100 kg: finger bar root bending {M_bar/1000:.0f} N m -> {M_bar/Zs:.1f} MPa (PETG printed on its side: ok; upright: marginal)")
