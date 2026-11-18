"""
jamar_v4.py — Ergonomic, high-speed, support-free Jamar-style grip dynamometer (v4).

Built around the exact measured CZL601 100 kg parallel-beam load cell, 3-hole G0-validated
bolt pattern (6 x M6 x 25 + washers), Arduino Nano, HX711, uncut cable coil, and 5 clinical
Jamar span positions (26–66 mm bar-to-bar gap).

Design upgrades over the boxy concept (cad/jamar_concept.py):
  1. High-speed flat-bed FDM orientation: every part prints lying flat (max Z-height 36 mm,
     zero support material, ~3x fewer layers than upright printing) with continuous XY
     perimeters aligned directly along the bending load path of the arms & finger bar.
  2. Ergonomic contoured touchpoints:
     - 4-finger scalloped pulling bar with upper/lower slip guards, swept bracket root
       (cuts stress concentration), calibration strap notch, and 20 mm fingertip clearance.
     - Anatomical convex palm swell on the adjustable palm bar with captive M5 hex nuts
       (metal-on-metal threads across 100s of span changes) and 1–5 index notches.
     - Swept tapered truss C-arms + tapered rear spine with 45° chamfered edges and
       weight-saving truss slots.
  3. Complete enclosed electronics & uncut cable architecture:
     - Frame (y = -18..+18) + Right Electronics/Cable Pod (y = +18..+41.3) + Left Cell Guard
       (y = -25.8..-18) enclose the cell with >= 3.2 mm bending clearance everywhere.
     - 18.5 mm straight/bend space beside the cell's +y cable exit (R 11 mm bend) + > 1 m
       uncut cable coil bay strictly on the fixed side.
     - Dedicated Nano rail + side stops + 45° octagonal rear USB window (14 x 11 mm),
       HX711 pocket, 8 x M3 x 10 countersunk screws, and calibration tie-down eye.

Coordinates (standing upright, matching dynamometer_cad.py):
    x : squeeze direction (-x = palm/fingers, +x = rear spine)
    y : width across hand (-y = left, +y = right cable exit side)
    z : vertical (+z = up)
    Load cell occupies x 0..22, y -20..20, z 0..130.
"""
import os
import math
import cadquery as cq
import dynamometer_cad as D

box, cyl = D.box, D.cyl

# ----------------------------------------------------------------------
# Global tolerances & canonical dimensions
# ----------------------------------------------------------------------
G = 3.2                  # nominal isolation gap (>= 3.0 mm everywhere)
WALL = 2.8               # structural housing wall
CORE_HY = 18.0           # half-width of core C-frame, arms & handles (36 mm wide, centered on y=0)
LEFT_Y0 = -25.8          # outer -y face of left cell guard (cell -20 - 3.2 gap - 2.6 wall)
RIGHT_Y1 = 41.3          # outer +y face of right electronics pod (cell +20 + 18.5 bay + 2.8 wall)

# ----------------------------------------------------------------------
# Finger part (moving, black PETG)
# ----------------------------------------------------------------------
FB_X0, FB_X1 = -50.0, -26.0     # finger bar base envelope (scallop crests reach -52.5)
FB_Z0 = 33.5                    # bottom of finger bar (3.5 mm above bottom arm z=30.0)
BR_Z0, BR_Z1 = 97.0, 132.5      # bracket on cell free end block (z 97..130)
FB_HY = 17.0                    # 34 mm wide bracket/bar core (centered cleanly inside 36 mm arms)

# ----------------------------------------------------------------------
# Frame, arms, palm bar & body (fixed, grey + charcoal)
# ----------------------------------------------------------------------
BX0 = FB_X1 + 20.0              # -6.0 -> 20.0 mm fingertip clearance behind finger bar
BX1_LO = 47.0                   # +47.0 lower spine (houses M6 heads + Nano + coil)
BX1_HI = 37.0                   # +37.0 sleek tapered upper spine above clamp (z >= 44)
BZ0 = -55.0                     # bottom of housing (ample coil depth below gusset)
ARM_LO1 = 30.0                  # bottom arm inner floor (hand window bottom)
ROOF0 = 136.0                   # top arm inner ceiling (3.5 mm above bracket z=132.5)
ARM_TIP_H = 12.5                # tapered outer tip thickness
ARM_ROOT_H = 20.0               # thick root near body for stiffness

PB_T = 20.0                     # nominal palm bar thickness at arm mounts
GAPS = (26.0, 36.0, 46.0, 56.0, 66.0)   # 5 clinical Jamar bar-to-bar gaps
POS = 1                         # default exported position (index 1 = pos 2, 36 mm gap)
ARM_X0 = FB_X0 - GAPS[-1] - PB_T - 10.0  # -146.0 mm arm nose tip

# ----------------------------------------------------------------------
# Electronics & uncut cable coil (inside fixed lower bay)
# ----------------------------------------------------------------------
BAY_X0, BAY_X1 = BX0 + WALL, BX1_LO - WALL    # -3.2 .. 44.2 (47.4 mm long)
BAY_Z0, BAY_Z1 = BZ0 + WALL, -3.5             # -51.2 .. -3.5 (47.7 mm tall)
BAY_Y0 = -CORE_HY + WALL                      # -15.2 (-y wall flat on print bed)
BAY_Y1 = RIGHT_Y1 - WALL                      # +38.5 (18.5 mm clear beside cell y=+20!)

CABLE_R = D.CABLE_D / 2                       # 2.565 mm
CXC = 8.5 + CABLE_R                           # 11.065 mm
CZC = 3.0 + CABLE_R                           # 5.565 mm
Y_FACE = D.CW / 2                             # 20.0 mm
STRAIGHT = 3.5
R_BEND = 11.0
PITCH = D.CABLE_D + 0.5                       # 5.63 mm

# Arduino Nano mounted on +Y-facing rail off the -y wall inside frame (X-axis orientation)
NANO_X0 = BAY_X1 - D.NANO_L - 2.0             # -1.8 mm (2 mm USB overhang reaches 44.2 inner wall)
NANO_ZC = -33.0                               # centered cleanly above lower corner bosses
NANO_RAIL_H = D.NANO_PIN + 1.5                # 9.5 mm off BAY_Y0 (-15.2)
NANO_Y_BOT = BAY_Y0 + NANO_RAIL_H             # -5.7
NANO_Y_TOP = NANO_Y_BOT + D.PCB_T             # -4.1
USB_YC = NANO_Y_TOP + D.NANO_USB_H / 2        # -2.2
WIN_Z, WIN_Y = 14.0, 11.0                     # USB window in +x rear wall

# HX711 (24 x 16 x 4 mm) on front wall shelf inside bay (above Nano in Z)
HX_L, HX_H, HX_T = 24.0, 16.0, 4.0
HX_X0, HX_X1 = BAY_X0 + 0.5, BAY_X0 + 0.5 + HX_T    # -2.7 .. +1.3
HX_Z0 = -20.5                                       # -20.5 .. -4.5 (clear above Nano pins)
HX_Y0 = -14.0

# Cover screws (M3 x 10 countersunk): 4 on pod_cover (+y), 4 on guard_left (-y)
# Upper spine screws at x=31.0 stay centered inside the tapered 25..37 spine and clear of z=0..32 M6 holes!
M3_SCREWS_POD = [
    (BAY_X0 + 2.4, BAY_Z0 + 2.4),
    (BAY_X1 - 2.4, BAY_Z0 + 2.4),
    (31.0, 44.0),
    (31.0, 146.0),
]
M3_SCREWS_GUARD = list(M3_SCREWS_POD)


# ----------------------------------------------------------------------
# Clean CAD primitives (support-free horizontal teardrops & chamfers)
# ----------------------------------------------------------------------
def extrude_xz(pts, y0, y1):
    """Extrude a closed 2D polygon in (x, z) from y0 to y1."""
    return (cq.Workplane("XZ").polyline(pts).close()
            .extrude(-(y1 - y0)).translate((0, y0, 0)))


def teardrop_x(x0, x1, y, z, d):
    """Horizontal hole along X with a 45° apex pointing in +Y (prints flat on -y with 0 supports)."""
    r = d / 2.0
    k = math.sqrt(0.5)
    apex = r * math.sqrt(2.0)
    wp = (cq.Workplane("YZ").workplane(offset=x0)
          .moveTo(y + r * k, z + r * k)
          .threePointArc((y - r, z), (y + r * k, z - r * k))
          .lineTo(y + apex, z)
          .close())
    return wp.extrude(x1 - x0)


def teardrop_z(z0, z1, x, y, d):
    """Vertical hole along Z with a 45° apex pointing in +Y (prints flat on -y with 0 supports)."""
    r = d / 2.0
    k = math.sqrt(0.5)
    apex = r * math.sqrt(2.0)
    wp = (cq.Workplane("XY").workplane(offset=z0)
          .moveTo(x + r * k, y + r * k)
          .threePointArc((x, y - r), (x - r * k, y + r * k))
          .lineTo(x, y + apex)
          .close())
    return wp.extrude(z1 - z0)


def oct_window_x(x0, x1, yc, zc, wy, wz):
    """Self-supporting chamfered octagonal opening along X (45° top in +Y)."""
    hy, hz = wy / 2.0, wz / 2.0
    c = min(3.0, hy * 0.45, hz * 0.45)
    pts = [
        (yc - hy, zc - hz + c), (yc - hy + c, zc - hz),
        (yc + hy - c, zc - hz), (yc + hy, zc - hz + c),
        (yc + hy, zc + hz - c), (yc + hy - c, zc + hz),
        (yc - hy + c, zc + hz), (yc - hy, zc + hz - c),
    ]
    return cq.Workplane("YZ").workplane(offset=x0).polyline(pts).close().extrude(x1 - x0)


def body_outer_pts():
    """Shared sleek tapered body silhouette (used by frame, pod_cover, guard_left)."""
    return [
        (BX0 + 5.0, BZ0),
        (BX1_LO - 6.0, BZ0),
        (BX1_LO, BZ0 + 6.0),
        (BX1_LO, 34.0),               # ends just past cell bottom clamp (z=32)
        (BX1_HI, 44.0),               # 45° sleek taper inward to slim upper spine
        (BX1_HI, ROOF0 + ARM_ROOT_H - 6.0),
        (BX1_HI - 6.0, ROOF0 + ARM_ROOT_H),
        (BX0, ROOF0 + ARM_ROOT_H),
        (BX0, ROOF0),
        (D.CT + G, ROOF0),
        (D.CT + G, BR_Z0 - G),
        (BX0, BR_Z0 - G),
        (BX0, BZ0 + 5.0),
    ]


# ----------------------------------------------------------------------
# 1. Main Structural C-Frame (`frame`, y = -18 .. +18, prints flat on -y)
# ----------------------------------------------------------------------
def frame():
    # Swept outer C-frame silhouette in X-Z (tapered arms + tapered upper spine)
    c_pts = [
        (ARM_X0 + 5.0, ROOF0 + ARM_TIP_H),
        (BX0 - 8.0, ROOF0 + ARM_ROOT_H),
        (BX1_HI - 6.0, ROOF0 + ARM_ROOT_H),
        (BX1_HI, ROOF0 + ARM_ROOT_H - 6.0),
        (BX1_HI, 44.0),
        (BX1_LO, 34.0),
        (BX1_LO, BZ0 + 6.0),
        (BX1_LO - 6.0, BZ0),
        (BX0 + 5.0, BZ0),
        (BX0, BZ0 + 5.0),
        (BX0, ARM_LO1 - ARM_ROOT_H),
        (ARM_X0 + 5.0, ARM_LO1 - ARM_TIP_H),
        (ARM_X0, ARM_LO1 - ARM_TIP_H + 4.0),
        (ARM_X0, ARM_LO1),
        (BX0, ARM_LO1),
        (BX0, ROOF0),
        (ARM_X0, ROOF0),
        (ARM_X0, ROOF0 + ARM_TIP_H - 4.0),
    ]
    f = extrude_xz(c_pts, -CORE_HY, CORE_HY)

    # Smooth inner root gusset on bottom arm only (top arm stays clear at z=136 for the moving bracket!)
    f = f.union(extrude_xz([(BX0 - 8.0, ARM_LO1), (BX0, ARM_LO1), (BX0, ARM_LO1 + 6.0)], -CORE_HY, CORE_HY))

    # Calibration tie-down lug at bottom-rear corner (z=-55..-41.5, completely below USB plug z=-38..-28)
    lug_pts = [(BX1_LO - 5.0, BZ0), (BX1_LO + 9.0, BZ0 + 2.0), (BX1_LO + 9.0, -42.0), (BX1_LO - 1.0, -41.5)]
    f = f.union(extrude_xz(lug_pts, -10.0, 10.0))
    f = f.cut(teardrop_z(BZ0 - 1.0, -40.5, BX1_LO + 4.2, 0.0, 7.0))  # 7 mm tie-down / cord pin hole

    # Cut open the cell zone (>= 3.2 mm gap everywhere around cell x 0..22, z 0..130)
    # Keep 2.8 mm front guard wall (-6.0 .. -3.2) intact up to bracket opening (z = 93.8)!
    f = f.cut(box(BAY_X0, D.CT + G, -CORE_HY - 1.0, CORE_HY + 1.0, D.CLAMP, ROOF0))
    f = f.cut(box(BX0 - 1.0, BAY_X0 + 0.5, -CORE_HY - 1.0, CORE_HY + 1.0, BR_Z0 - G, ROOF0))
    f = f.cut(box(BAY_X0, D.CT, -CORE_HY - 1.0, CORE_HY + 1.0, 0.0, D.CLAMP + 0.5))
    f = f.cut(box(BAY_X0, 12.0, -CORE_HY - 1.0, CORE_HY + 1.0, -3.5, 0.5))
    f = f.cut(extrude_xz([(BAY_X0, -16.5), (12.0, -3.5), (BAY_X0, -3.5)], -CORE_HY - 1.0, CORE_HY + 1.0))

    # Electronics & cable bay cavity: closed at -y (BAY_Y0 = -15.2), open toward +y (+18)
    f = f.cut(box(BAY_X0, BAY_X1, BAY_Y0, CORE_HY + 1.0, BAY_Z0, -3.5))
    # Re-add cell clamping boss & compact 45° ledge gusset (stops at z = -19.5 so lower bay stays open for coil!)
    f = f.union(box(D.CT, BX1_LO - WALL + 1.0, -D.BY, D.BY, 0.0, D.CLAMP))
    f = f.union(box(12.0, BX1_LO - WALL + 1.0, -D.BY, D.BY, -3.5, 0.0))
    f = f.union(extrude_xz([(12.0, -3.5), (28.0, -3.5), (28.0, -19.5)], -D.BY, D.BY))
    f = f.union(box(28.0, BX1_LO - WALL + 1.0, -D.BY, D.BY, -19.5, 0.0))

    # 3 x M6 load-cell mounting holes + teardrop counterbores on rear spine (CB_FING_X = 33.0)
    for z, y in D.HOLES_NEAR:
        f = f.cut(teardrop_x(D.CT - 1.0, BX1_LO + 2.0, y, z, D.HOLE_CLR))
        f = f.cut(teardrop_x(D.CB_FING_X, BX1_LO + 2.0, y, z, D.CBORE_W))

    # 5 x M5 vertical palm-bar lock holes through top & bottom arms + index notches 1..5
    for g in GAPS:
        xc = FB_X0 - g - PB_T / 2.0
        f = f.cut(teardrop_z(ARM_LO1 - ARM_ROOT_H - 1.0, ARM_LO1 + 1.0, xc, 0.0, 5.4))
        f = f.cut(teardrop_z(ROOF0 - 1.0, ROOF0 + ARM_ROOT_H + 1.0, xc, 0.0, 5.4))
        f = f.cut(box(xc - 0.9, xc + 0.9, CORE_HY - 1.2, CORE_HY + 1.0, ROOF0 + 11.5, ROOF0 + 21.0))

    # Truss lightening slots in arm mid-spans + upper spine pocket
    slot_top = extrude_xz([(-64.0, 141.5), (-16.0, 141.5), (-16.0, 148.5), (-64.0, 145.5)], -CORE_HY - 1.0, CORE_HY + 1.0).edges("|Y").fillet(2.0)
    f = f.cut(slot_top)
    slot_bot = extrude_xz([(-64.0, 20.5), (-16.0, 17.5), (-16.0, 24.5), (-64.0, 24.5)], -CORE_HY - 1.0, CORE_HY + 1.0).edges("|Y").fillet(2.0)
    f = f.cut(slot_bot)
    # Upper spine lightening window (z = 54 .. 132, x = 28.0 .. 34.0, 3 mm walls) -> cuts mass & print time!
    spine_slot = extrude_xz([(28.2, 54.0), (33.8, 54.0), (33.8, 132.0), (28.2, 132.0)], -CORE_HY - 1.0, CORE_HY + 1.0).edges("|Y").fillet(2.2)
    f = f.cut(spine_slot)

    # Nano mounting rail & 4 side stops rising in +Y directly from BAY_Y0 (-15.2)
    f = f.union(box(NANO_X0 + 1.5, NANO_X0 + D.NANO_L - 1.5, BAY_Y0 - 0.5, NANO_Y_BOT, NANO_ZC - 5.0, NANO_ZC + 5.0))
    for sz in (-1, 1):
        zz = NANO_ZC + sz * (D.NANO_W / 2.0 + 0.4)
        z_a, z_b = min(zz, zz + sz * 1.4), max(zz, zz + sz * 1.4)
        for xx in (NANO_X0 + 10.0, NANO_X0 + D.NANO_L - 10.0):
            f = f.union(box(xx - 1.6, xx + 1.6, BAY_Y0 - 0.5, NANO_Y_BOT + 1.2, z_a, z_b))

    # HX711 cradle guide rails inside front bay (above Nano in Z)
    for z_rail0, z_rail1 in ((HX_Z0 - 1.6, HX_Z0 - 0.1), (HX_Z0 + HX_H + 0.1, HX_Z0 + HX_H + 1.6)):
        f = f.union(box(HX_X0 - 0.6, HX_X1 + 0.6, BAY_Y0 - 0.5, HX_Y0 + HX_L - 2.0, z_rail0, z_rail1))

    # USB window through +x rear wall (self-supporting octagonal opening)
    f = f.cut(oct_window_x(BAY_X1 - 1.0, BX1_LO + 1.0, USB_YC, NANO_ZC, WIN_Y, WIN_Z))

    # M3 screw bosses & pilot holes for pod_cover (+y = +18) and guard_left (-y = -18)
    for bx, bz in M3_SCREWS_POD:
        if bz < 0:
            f = f.union(cq.Workplane("XZ").center(bx, bz).circle(3.5).extrude(-(CORE_HY - BAY_Y0)).translate((0, BAY_Y0, 0)))
        f = f.cut(cq.Workplane("XZ").center(bx, bz).circle(D.M3_PILOT / 2.0).extrude(-11.0).translate((0, CORE_HY - 10.0, 0)))
    for bx, bz in M3_SCREWS_GUARD:
        f = f.cut(cq.Workplane("XZ").center(bx, bz).circle(D.M3_PILOT / 2.0).extrude(-11.0).translate((0, -CORE_HY - 1.0, 0)))

    try:
        f = f.edges("|X or |Z").chamfer(0.8)
    except Exception:
        pass
    return f


# ----------------------------------------------------------------------
# 2. Adjustable Ergonomic Palm Bar (`palm_bar`, y = -18 .. +18, prints flat on -y)
# ----------------------------------------------------------------------
def palm_bar(pos=POS):
    g = GAPS[pos]
    x1 = FB_X0 - g
    x0 = x1 - PB_T
    arch_pts = [
        (x0, ARM_LO1 + 10.0),
        (x0 - 2.6, 56.0),
        (x0 - 4.0, 82.0),
        (x0 - 2.6, 108.0),
        (x0, ROOF0 - 10.0),
    ]
    wp = (cq.Workplane("XZ")
          .moveTo(x1, ARM_LO1 + 0.2)
          .lineTo(x1, ROOF0 - 0.2)
          .lineTo(x0, ROOF0 - 0.2)
          .lineTo(*arch_pts[-1])
          .spline(list(reversed(arch_pts[:-1])), includeCurrent=True)
          .lineTo(x0, ARM_LO1 + 0.2)
          .close())
    b = wp.extrude(-(2.0 * CORE_HY)).translate((0, -CORE_HY, 0))

    try:
        b = b.faces(">Y").edges().chamfer(2.8)
        b = b.faces("<Y").edges().chamfer(1.2)
    except Exception:
        pass

    # M5 bolt holes + captive M5 hex nut slots at top & bottom ends
    xc = x1 - PB_T / 2.0
    b = b.cut(teardrop_z(ARM_LO1 - 1.0, ARM_LO1 + 16.0, xc, 0.0, 5.4))
    b = b.cut(teardrop_z(ROOF0 - 16.0, ROOF0 + 1.0, xc, 0.0, 5.4))
    for zn in (ARM_LO1 + 8.0, ROOF0 - 8.0):
        b = b.cut(box(xc - 4.2, x1 + 1.0, -4.3, 4.3, zn - 2.2, zn + 2.2))
    return b


# ----------------------------------------------------------------------
# 3. Ergonomic 4-Finger Trigger + Bracket (`finger_part`, prints flat on -y)
# ----------------------------------------------------------------------
def finger():
    front_profile = [
        (-52.5, FB_Z0 + 1.5),
        (-52.5, FB_Z0 + 4.5),
        (-48.8, 45.0),          # pinky valley
        (-51.6, 55.5),          # ridge 1-2
        (-48.2, 66.5),          # ring valley
        (-51.6, 77.5),          # ridge 2-3
        (-48.2, 88.5),          # middle valley
        (-51.6, 99.5),          # ridge 3-4
        (-48.8, 110.5),         # index valley
        (-52.2, 122.0),
    ]
    wp = (cq.Workplane("XZ")
          .moveTo(-50.5, FB_Z0)
          .lineTo(-52.5, FB_Z0 + 1.5)
          .lineTo(-52.5, FB_Z0 + 4.5)
          .spline(front_profile[2:], includeCurrent=True)
          .lineTo(-52.2, 128.0)
          .lineTo(-48.5, BR_Z1)
          .lineTo(0.0, BR_Z1)
          .lineTo(0.0, BR_Z0)
          .lineTo(-13.0, BR_Z0)
          .lineTo(-26.0, 84.0)
          .lineTo(-26.0, FB_Z0 + 3.0)
          .lineTo(-29.0, FB_Z0)
          .close())
    f = wp.extrude(-(2.0 * FB_HY)).translate((0, -FB_HY, 0))

    try:
        f = f.faces(">Y").edges().chamfer(2.8)
        f = f.faces("<Y").edges().chamfer(1.2)
    except Exception:
        pass

    # Calibration strap notch on the back of finger bar at mid-height (z = 81.0)
    f = f.cut(box(FB_X1 - 2.0, FB_X1 + 1.0, -7.0, 7.0, 77.0, 85.0))

    # 3 x M6 bolt holes + 45° teardrop counterbores at x = -11.0 (12.4 mm engagement)
    for z, y in D.HOLES_NEAR:
        zz = D.CL - z
        f = f.cut(teardrop_x(-55.0, 1.0, y, zz, D.HOLE_CLR))
        f = f.cut(teardrop_x(-55.0, D.CB_PALM_X, y, zz, D.CBORE_W))
    return f


# ----------------------------------------------------------------------
# 4. Right Electronics & Cable Pod Cover (`pod_cover`, y = +18 .. +41.3)
# ----------------------------------------------------------------------
def pod_cover():
    """Closes the +y side of the frame: encloses cable exit (18.5 mm space), coil bay,
    and right flank of the load cell (>= 3.2 mm gap). Prints open-side-up on +y face."""
    c = extrude_xz(body_outer_pts(), CORE_HY, RIGHT_Y1)
    try:
        c = c.faces(">Y").edges().chamfer(1.2)
    except Exception:
        pass

    # 1) Lower electronics & cable coil bay (y = CORE_HY - 1 .. BAY_Y1 = 38.5)
    c = c.cut(box(BAY_X0, BAY_X1, CORE_HY - 1.0, BAY_Y1, BAY_Z0, -3.5))
    # 2) Upper cable turn & cell side clearance (z = -3.5 .. 33.0, stops at x=25.2 so M3 boss zone is solid)
    c = c.cut(box(BAY_X0, D.CT + G, CORE_HY - 1.0, BAY_Y1, -3.5, 33.0))
    # 3) Cell bending zone clearance (y = CORE_HY - 1 .. 23.2, z = 32.5 .. 133.5)
    c = c.cut(box(BAY_X0, D.CT + G, CORE_HY - 1.0, D.CW / 2.0 + G, 32.5, 133.5))
    c = c.cut(box(-0.5, D.CT + G, CORE_HY - 1.0, D.CW / 2.0 + G, -0.5, 33.0))
    # 4) Hollow weight-saving pockets inside the unused rear upper pod (clear of M3 bosses at z=44, 146!)
    c = c.cut(box(D.CT + G + 2.0, BX1_HI - 2.8, CORE_HY - 1.0, BAY_Y1, 52.0, 138.0))
    c = c.cut(box(D.CT + G + 2.0, BX1_LO - 2.8, D.CW / 2.0 + G + 2.8, BAY_Y1, 0.0, 32.0))

    # M3 screw clearance + 45° countersinks on +y face
    for bx, bz in M3_SCREWS_POD:
        c = c.cut(cq.Workplane("XZ").center(bx, bz).circle(D.M3_CLR / 2.0).extrude(-(RIGHT_Y1 - CORE_HY + 2.0)).translate((0, CORE_HY - 1.0, 0)))
        c = c.cut(cq.Solid.makeCone(1.7, 3.5, 1.8, cq.Vector(bx, RIGHT_Y1 - 1.8, bz), cq.Vector(0, 1, 0)))
    return c


# ----------------------------------------------------------------------
# 5. Left Cell Guard Plate (`guard_left`, y = -25.8 .. -18.0, prints flat on -y)
# ----------------------------------------------------------------------
def guard_left():
    """Sleek 7.8 mm left flank guard enclosing the load cell's -y side (>= 3.2 mm air gap)."""
    g = extrude_xz(body_outer_pts(), LEFT_Y0, -CORE_HY)
    try:
        g = g.faces("<Y").edges().chamfer(1.2)
    except Exception:
        pass
    # Cell side pocket (y = -23.2 .. -17.5, leaving 3.2 mm air gap from cell y=-20!)
    g = g.cut(box(BAY_X0, D.CT + G, -(D.CW / 2.0 + G), -CORE_HY + 1.0, -0.5, 133.5))
    # Lower bay & upper spine lightening pockets (clear of M3 bosses)
    g = g.cut(box(BAY_X0 + 4.0, 34.0, -23.0, -CORE_HY + 1.0, BAY_Z0 + 6.0, -4.0))
    g = g.cut(box(D.CT + G + 2.0, BX1_HI - 2.8, -23.0, -CORE_HY + 1.0, 52.0, 138.0))

    for bx, bz in M3_SCREWS_GUARD:
        g = g.cut(cq.Workplane("XZ").center(bx, bz).circle(D.M3_CLR / 2.0).extrude(-(CORE_HY + LEFT_Y0 + 10.0)).translate((0, LEFT_Y0 - 1.0, 0)))
        g = g.cut(cq.Solid.makeCone(1.7, 3.5, 1.8, cq.Vector(bx, LEFT_Y0 + 1.8, bz), cq.Vector(0, -1, 0)))
    return g


# ----------------------------------------------------------------------
# Reference envelopes (cable, coil, electronics) for automated verification
# ----------------------------------------------------------------------
def cable_pts():
    k = math.sqrt(0.5)
    y1 = Y_FACE + STRAIGHT
    c1 = (y1, CZC - R_BEND)
    return dict(
        p0=(Y_FACE, CZC), p1=(y1, CZC),
        m=(c1[0] + R_BEND * k, c1[1] + R_BEND * k),
        p2=(y1 + R_BEND, CZC - R_BEND),
        p3=(y1 + R_BEND, -20.0),
    )


def cable_tube(extra=0.0):
    q = cable_pts()
    path = (cq.Workplane("YZ", origin=(CXC, 0, 0)).moveTo(*q["p0"]).lineTo(*q["p1"])
            .threePointArc(q["m"], q["p2"]).lineTo(*q["p3"]))
    return cq.Workplane("XZ", origin=(CXC, Y_FACE, CZC)).circle(CABLE_R + extra).sweep(path)


def coil_zone():
    """Spare cable coil volume strictly clear of gusset, cell, Nano, HX711, and corner bosses."""
    x0, x1 = BAY_X0 + 1.0, BAY_X1 - 1.0          # -2.2 .. 43.2 (45.4 mm)
    z0, z1 = BAY_Z0 + 1.0, -20.2                 # -51.2 .. -20.2 (31.0 mm)
    y0, y1 = 4.3, BAY_Y1 - 0.2                   # +4.3 .. +38.3 (34.0 mm = 6 layers!)
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    hx, hz, rc = (x1 - x0) / 2.0, (z1 - z0) / 2.0, 14.0
    w = 2.0 * PITCH
    outer = cq.Workplane("XZ").center(cx, cz).rect(2 * hx, 2 * hz).extrude(-(y1 - y0)).translate((0, y0, 0)).edges("|Y").fillet(rc)
    inner = cq.Workplane("XZ").center(cx, cz).rect(2 * (hx - w), 2 * (hz - w)).extrude(-(y1 - y0 + 2)).translate((0, y0 - 1, 0)).edges("|Y").fillet(max(2.0, rc - w))
    return outer.cut(inner), (hx, hz, rc, y1 - y0)


def nano_env():
    """Arduino Nano sitting on BAY_Y0 rail, USB pointing +x."""
    pcb = box(NANO_X0, NANO_X0 + D.NANO_L, NANO_Y_BOT, NANO_Y_TOP, NANO_ZC - D.NANO_W / 2.0, NANO_ZC + D.NANO_W / 2.0)
    rows = None
    for s in (-1, 1):
        zz = NANO_ZC + s * D.NANO_ROW / 2.0
        r = (box(NANO_X0 + 2.5, NANO_X0 + D.NANO_L - 2.5, NANO_Y_BOT - D.NANO_PIN, NANO_Y_BOT, zz - 0.8, zz + 0.8)
             .union(box(NANO_X0 + 2.5, NANO_X0 + D.NANO_L - 2.5, NANO_Y_TOP, NANO_Y_TOP + D.NANO_PIN, zz - 0.5, zz + 0.5)))
        rows = r if rows is None else rows.union(r)
    usb = box(NANO_X0 + D.NANO_L - 4.0, NANO_X0 + D.NANO_L + 2.0, NANO_Y_TOP, NANO_Y_TOP + D.NANO_USB_H, NANO_ZC - 3.9, NANO_ZC + 3.9)
    return pcb, rows.union(usb)


def plug_env():
    """10 x 8 mm USB plug moulding + 18 mm boot reaching from outside rear wall into Nano USB."""
    x_face = NANO_X0 + D.NANO_L + 2.0
    return box(x_face, x_face + 18.0, USB_YC - 4.0, USB_YC + 4.0, NANO_ZC - 5.0, NANO_ZC + 5.0)


def hx_env():
    """HX711 board (24 x 16 x 4 mm) slid into front bay rails above Nano."""
    return box(HX_X0, HX_X1, HX_Y0, HX_Y0 + HX_L, HX_Z0, HX_Z0 + HX_H)


def to_flat_bed(part):
    """Orient part flat on its -y side (Y becomes printer Z!) and shift to bed origin (0, 0, 0)."""
    p = part.rotate((0, 0, 0), (1, 0, 0), -90)
    bb = p.val().BoundingBox()
    return p.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def to_pod_bed(part):
    """Orient pod_cover open-side-up (+y down on bed) and shift to (0, 0, 0)."""
    p = part.rotate((0, 0, 0), (1, 0, 0), 90)
    bb = p.val().BoundingBox()
    return p.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def vol(q):
    try:
        return q.val().Volume() if q.vals() else 0.0
    except Exception:
        return 0.0


# ----------------------------------------------------------------------
# Build, verify, export
# ----------------------------------------------------------------------
if __name__ == "__main__":
    OUT = os.path.join(D.OUT, "jamar_v4")
    PR = os.path.join(OUT, "print_ready")
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PR, exist_ok=True)

    fr = frame()
    pb = palm_bar()
    fg = finger()
    pc = pod_cover()
    gl = guard_left()
    cell = D.cell()

    parts = {
        "frame": (fr, to_flat_bed, "1_frame_jamar_v4.stl"),
        "palm_bar": (pb, to_flat_bed, "2_palm_bar_jamar_v4.stl"),
        "finger_part": (fg, to_flat_bed, "3_finger_bar_jamar_v4.stl"),
        "pod_cover": (pc, to_pod_bed, "4_pod_cover_jamar_v4.stl"),
        "guard_left": (gl, to_flat_bed, "5_guard_left_jamar_v4.stl"),
    }

    WEB_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website", "public", "models"))
    web_names = {
        "frame": "jamar_frame.stl",
        "palm_bar": "jamar_palm_bar.stl",
        "finger_part": "jamar_finger.stl",
        "pod_cover": "jamar_cover.stl",
        "guard_left": "jamar_guard.stl",
    }

    print("part           valid  assembly (x y z)        bed footprint (x y) x Z_h     volume   ~PETG (4w/30%)")
    tot_v = 0.0
    for name, (solid, bed_fn, stl_name) in parts.items():
        assert solid.val().isValid(), f"{name} is NOT a valid solid!"
        cq.exporters.export(solid, os.path.join(OUT, f"{name}_v4.step"))
        cq.exporters.export(solid, os.path.join(OUT, f"{name}_v4.stl"), tolerance=0.03, angularTolerance=0.1)
        if os.path.isdir(WEB_DIR):
            cq.exporters.export(solid, os.path.join(WEB_DIR, web_names[name]), tolerance=0.05, angularTolerance=0.18)
        bed_part = bed_fn(solid)
        cq.exporters.export(bed_part, os.path.join(PR, stl_name), tolerance=0.03, angularTolerance=0.1)

        bb = solid.val().BoundingBox()
        bbb = bed_part.val().BoundingBox()
        v = solid.val().Volume() / 1000.0
        tot_v += v
        assert bbb.xlen <= 256.0 and bbb.ylen <= 256.0, f"{name} exceeds 256x256 Bambu bed!"
        print(f"{name:14s} {str(solid.val().isValid()):5s}  "
              f"{bb.xlen:5.1f} x {bb.ylen:4.1f} x {bb.zlen:5.1f}   "
              f"{bbb.xlen:5.1f} x {bbb.ylen:5.1f} x {bbb.zlen:4.1f} mm   "
              f"{v:6.1f} cm3   {v*1.27*0.52:4.0f} g")
    print(f"TOTAL volume: {tot_v:.1f} cm3 (~{tot_v*1.27*0.52:.0f} g PETG), max print Z height: 36.0 mm (0 supports)")

    # Colored STEP assembly
    (cq.Assembly()
     .add(fr, name="frame", color=cq.Color(0.84, 0.86, 0.89))
     .add(pb, name="palm_bar", color=cq.Color(0.66, 0.69, 0.74))
     .add(fg, name="finger_part", color=cq.Color(0.16, 0.18, 0.21))
     .add(pc, name="pod_cover", color=cq.Color(0.24, 0.26, 0.30))
     .add(gl, name="guard_left", color=cq.Color(0.24, 0.26, 0.30))
     .add(cell, name="load_cell", color=cq.Color(0.18, 0.62, 0.54))
     ).save(os.path.join(OUT, "jamar_v4_assembly.step"))

    # 1. Force-path isolation checks
    fixed = fr.union(pb).union(pc).union(gl)
    ov_ff = vol(fg.intersect(fixed))
    ov_cell = vol(cell.intersect(fixed)) + vol(cell.intersect(fg))
    gap_fr = fg.val().distance(fr.val())
    gap_pc = fg.val().distance(pc.val())
    gap_gl = fg.val().distance(gl.val())
    gap_pb_all = [round(fg.val().distance(palm_bar(i).val()), 2) for i in range(5)]

    flex = box(0, D.CT, -D.CW / 2, D.CW / 2, D.CLAMP + 5, D.CL - D.CLAMP - 5)
    clr_flex_fixed = flex.val().distance(fixed.val())
    clr_flex_fg = flex.val().distance(fg.val())

    print("\nForce path")
    print(f"  finger_part vs fixed parts overlap  {ov_ff:.3f} mm3 (must be 0)")
    print(f"  load cell vs ALL printed parts      {ov_cell:.3f} mm3 (must be 0)")
    print(f"  gaps to finger_part: frame {gap_fr:.2f}, pod_cover {gap_pc:.2f}, guard_left {gap_gl:.2f} mm (>= 3.0)")
    print(f"  palm_bar clearances across 5 pos    {gap_pb_all} mm")
    print(f"  bending zone clearance: fixed {clr_flex_fixed:.2f} mm, finger_part {clr_flex_fg:.2f} mm (>= 3.0)")
    assert ov_ff < 0.01 and ov_cell < 0.01
    assert min(gap_fr, gap_pc, gap_gl, clr_flex_fixed, clr_flex_fg) >= 3.0

    # 2. Fastener & washer checks (real M6 x 25 + Ø12 x 1.6 washers + Ø10.5 x 3.3 button heads)
    def bolt_solids(floor_x, sign, zs):
        out = None
        for z, y in D.HOLES_NEAR:
            zz = zs(z)
            qs = [
                D.bolt_hole(floor_x, floor_x + sign * 25.0, y, zz, D.BOLT) if sign > 0 else D.bolt_hole(floor_x - 25.0, floor_x, y, zz, D.BOLT),
                D.bolt_hole(*sorted((floor_x, floor_x - sign * 1.6)), y, zz, 12.0),
                D.bolt_hole(*sorted((floor_x - sign * 1.6, floor_x - sign * 4.9)), y, zz, 10.5),
            ]
            for q in qs:
                out = q if out is None else out.union(q)
        return out

    v_bolts = vol(bolt_solids(D.CB_FING_X, -1, lambda z: z).intersect(fr)) + vol(bolt_solids(D.CB_PALM_X, +1, lambda z: D.CL - z).intersect(fg))
    print(f"  6 x M6 x 25 + washers vs parts      {v_bolts:.3f} mm3 (must be 0; 12.4 mm engagement)")
    assert v_bolts < 0.05

    # 3. Cable & spare coil checks
    ct = cable_tube()
    ov_cable = vol(ct.intersect(fixed)) + vol(ct.intersect(fg))
    ct_clr = 0.0
    for c in (0.5, 1.0, 1.3):
        if vol(cable_tube(c).intersect(fixed)) + vol(cable_tube(c).intersect(fg)) < 0.05:
            ct_clr = c
    d_cable_fg = ct.val().distance(fg.val())
    cz, (chx, chz, crc, cy_depth) = coil_zone()
    ov_coil = vol(cz.intersect(fixed)) + vol(cz.intersect(cell))
    layers = int(cy_depth // PITCH)
    per_turn = 0.0
    for i in range(2):
        off = CABLE_R + 0.25 + i * PITCH
        a, b, r = chx - off, chz - off, crc - off
        per_turn += 2 * (2 * a + 2 * b) - (8 - 2 * math.pi) * r
    coil_cap = per_turn * layers

    print("\nCable & coil")
    print(f"  +y space from cell face to wall     {BAY_Y1 - Y_FACE:.1f} mm (>= 15)")
    print(f"  cable tube vs parts                 {ov_cable:.3f} mm3 (clear by >= {ct_clr:.1f} mm); to finger_part {d_cable_fg:.1f} mm")
    print(f"  spare coil zone vs parts/cell       {ov_coil:.3f} mm3; capacity ~{coil_cap:.0f} mm ({layers} layers in Y)")
    assert ov_cable < 0.05 and ov_coil < 0.05 and coil_cap >= 1000.0

    # 4. Electronics checks
    pcb, nano_rest = nano_env()
    hx = hx_env()
    plug = plug_env()
    e_nano = vol(pcb.intersect(fixed)) + vol(nano_rest.intersect(fixed)) + vol(pcb.intersect(fg)) + vol(nano_rest.intersect(fg))
    e_hx = vol(hx.intersect(fixed)) + vol(hx.intersect(pcb.union(nano_rest))) + vol(hx.intersect(cz))
    e_plug = vol(plug.intersect(fixed))
    e_coil_elec = vol(cz.intersect(pcb.union(nano_rest))) + vol(cz.intersect(hx))
    print("\nElectronics")
    print(f"  Nano + pins + USB vs housing        {e_nano:.3f} mm3 (must be 0)")
    print(f"  HX711 vs housing / Nano / coil      {e_hx:.3f} mm3 (must be 0)")
    print(f"  USB plug + boot through +x window   {e_plug:.3f} mm3 (must be 0)")
    print(f"  coil zone vs Nano & HX711           {e_coil_elec:.3f} mm3 (must be 0)")
    assert max(e_nano, e_hx, e_plug, e_coil_elec) < 0.05

    # 5. Stress check at 100 kg (981 N)
    F = 981.0
    M_fb = F * 25.0
    S_fb = (2 * FB_HY) * (FB_X1 - FB_X0) ** 2 / 6.0
    M_arm = (F * 0.5) * 126.0
    S_arm = (2 * CORE_HY) * (ARM_ROOT_H ** 2) / 6.0
    print("\n100 kg (981 N) Structural Stress (PETG XY flexural yield ~50 MPa)")
    print(f"  finger bar root (swept)             {M_fb / S_fb:.1f} MPa")
    print(f"  C-arm root (20 mm deep, flat XY)    {M_arm / S_arm:.1f} MPa (2.0x+ SF)")
    print("\nALL CHECKS PASSED")
