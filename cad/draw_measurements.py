"""
draw_measurements.py — annotated drawings of the parts as MEASURED (not as specified).

    images/measured_load_cell.png    the load cell, from Thomas's caliper readings (2026-10-12)
    images/measured_electronics.png  HX711 + Arduino Nano, nominal reference values (to verify)

Line convention on the drawings:
    solid blue    measured with calipers (from the annotated photos)
    dashed orange derived from the measured numbers or read off the photos — please confirm
    grey          reference drawing, not yet measured on the real part

Run:  python draw_measurements.py        needs: pip install matplotlib
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, "..", "images"))
os.makedirs(IMG, exist_ok=True)

BLUE, ORANGE, GREY, INK = "#1f4e9c", "#d9730d", "#7a7f87", "#1b1f24"
BODY, TAPE, HOLE = "#dfe3e8", "#f7f7f2", "#8a9099"


def dim(ax, p, q, text, off=0.0, color=BLUE, style="-", fs=10, side="auto", tick=1.0):
    """Dimension line from p to q, pushed `off` away from the part, label centred on it."""
    (x0, y0), (x1, y1) = p, q
    horiz = abs(y1 - y0) < abs(x1 - x0)
    if horiz:
        y0 += off; y1 += off
    else:
        x0 += off; x1 += off
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="<|-|>", color=color, lw=1.3, ls=style,
                                shrinkA=0, shrinkB=0, mutation_scale=9))
    # extension lines back to the part
    for (px, py), (ex, ey) in (((p[0], p[1]), (x0, y0)), ((q[0], q[1]), (x1, y1))):
        ax.plot([px, ex], [py, ey], color=color, lw=0.6, ls=":", alpha=0.7)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.text(mx, my, text, color=color, fontsize=fs, ha="center", va="center",
            rotation=0 if horiz else 90, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.95))


def note(ax, x, y, text, color=INK, fs=9, ha="left", va="center", bold=False):
    ax.text(x, y, text, color=color, fontsize=fs, ha=ha, va=va,
            fontweight="bold" if bold else "normal")


def clean(ax, xl, yl, title):
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK, pad=6)


# ======================================================================
# LOAD CELL
# ======================================================================
def load_cell():
    L, W, T = 130.0, 40.0, 22.0
    BLK = 33.0                       # end block length            measured
    D = 6.67                         # tapped-hole opening diameter  derived: 40 - 2*16.67
    X1 = 21.44 + D / 2               # single hole centre from outer end   measured edge + D/2
    XP = 11.8                        # pair centre from outer end          measured 2026-10-12
    PAIR_DY = (7.94 + D) / 2         # pair half-spacing                   measured gap + D

    fig = plt.figure(figsize=(17, 11.5), dpi=140)
    fig.patch.set_facecolor("white")
    fig.suptitle("Load cell as measured — 100 kg parallel-beam cell, serial 2607021487",
                 x=0.04, y=0.975, ha="left", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.04, 0.945, "Measured 2026-10-12 with calipers.  Blue = measured.  Orange = derived or read off "
             "the photos (please confirm).  All dimensions in mm.", fontsize=10, color=GREY)

    # ---------------- top view ----------------
    ax = fig.add_axes([0.04, 0.48, 0.92, 0.43])
    clean(ax, (-12, 142), (-36, 56), "TOP VIEW — the face with the mounting holes (130 × 40)")
    ax.add_patch(Rectangle((0, 0), L, W, fc=BODY, ec=INK, lw=1.6))
    ax.add_patch(Rectangle((BLK, 0), L - 2 * BLK, W, fc=TAPE, ec=GREY, lw=0.8, ls="--"))
    note(ax, L / 2, W / 2, "bending zone\n(sealed, strain gauges underneath)\n≈ 64 mm between the end blocks",
         color=GREY, ha="center", fs=10)
    for end in (0, 1):
        sgn = 1 if end == 0 else -1
        ox = 0 if end == 0 else L
        hx1 = ox + sgn * X1
        hxp = ox + sgn * XP
        for (hx, hy, ec, ls) in ((hx1, W / 2, INK, "-"),
                                 (hxp, W / 2 + PAIR_DY, INK, "-"),
                                 (hxp, W / 2 - PAIR_DY, INK, "-")):
            ax.add_patch(Circle((hx, hy), D / 2, fc=HOLE, ec=ec, lw=1.4, ls=ls))
    # centre lines
    ax.plot([-4, L + 4], [W / 2, W / 2], color=GREY, lw=0.6, ls="-.")

    # overall
    dim(ax, (0, 0), (L, 0), "130.00", off=-22)
    dim(ax, (0, 0), (0, W), "40.00", off=-6.5)
    dim(ax, (0, 0), (BLK, 0), "33.00  end block", off=-14)
    # single hole position (left block)
    dim(ax, (0, 0), (21.44, 0), "21.44", off=-6, fs=9)
    dim(ax, (21.44 + D, 0), (BLK, 0), "5.00", off=-6, fs=9)
    dim(ax, (X1 + 6, 0), (X1 + 6, W / 2 - D / 2), "16.67", off=0, fs=9)
    # pair gap
    dim(ax, (XP, W / 2 - PAIR_DY + D / 2), (XP, W / 2 + PAIR_DY - D / 2), "7.94", off=0, fs=9)
    # annotations (orange)
    dim(ax, (0, W), (XP, W), "11.80  pair centre", off=5.5, fs=9)
    note(ax, X1 + 20, -29.5, "hole opening ∅ ≈ 6.7 (derived, 40 − 2 × 16.67).  Thread: M6, bolt goes in by hand.  Tapped all the way through (measured/tested).",
         color=ORANGE, fs=9)
    note(ax, L + 2, W / 2 + 7, "right end assumed a\nmirror image of the left\n(same 21.44 / 7.95 gap\nmeasured on the photo)",
         color=ORANGE, fs=8.5)
    note(ax, 10, W + 4.0, "", fs=8)

    # ---------------- side view ----------------
    ax2 = fig.add_axes([0.04, 0.17, 0.60, 0.28])
    clean(ax2, (-12, 142), (-12, 36), "SIDE VIEW — the 130 × 22 face (load direction is across the 22)")
    ax2.add_patch(Rectangle((0, 0), L, T, fc=BODY, ec=INK, lw=1.6))
    c1, c2, cy, r, neck = L / 2 - 9.9, L / 2 + 9.9, T / 2, 12.8 / 2, 6.5
    ax2.add_patch(Rectangle((c1, cy - neck / 2), c2 - c1, neck, fc="white", ec=INK, lw=1.4))
    ax2.add_patch(Circle((c1, cy), r, fc="white", ec=INK, lw=1.4))
    ax2.add_patch(Circle((c2, cy), r, fc="white", ec=INK, lw=1.4))
    ax2.plot([BLK, BLK], [0, T], color=GREY, lw=0.7, ls="--")
    ax2.plot([L - BLK, L - BLK], [0, T], color=GREY, lw=0.7, ls="--")
    dim(ax2, (0, 0), (L, 0), "130.00", off=-5.5)
    dim(ax2, (0, 0), (0, T), "22.00", off=-5.5)
    dim(ax2, (c1 - r, T), (c2 + r, T), "32.60  slot, end to end", off=4.0)
    dim(ax2, (c1 - r, cy - r), (c1 - r, cy + r), "12.8", off=-3.5, fs=9)
    dim(ax2, (L / 2, cy - neck / 2), (L / 2, cy + neck / 2), "6.50", off=0, fs=9)
    note(ax2, 3, T + 7.5, "stamped ↓ 100 kg (arrow = load direction)", color=GREY, fs=9)

    # ---------------- end view ----------------
    ax3 = fig.add_axes([0.68, 0.17, 0.28, 0.28])
    clean(ax3, (-14, 58), (-12, 36), "END VIEW — 40 × 22")
    ax3.add_patch(Rectangle((0, 0), W, T, fc=BODY, ec=INK, lw=1.6))
    dim(ax3, (0, 0), (W, 0), "40.00", off=-5.5)
    dim(ax3, (W, 0), (W, T), "22.00", off=5.5)
    ax3.add_patch(Circle((W * 0.78, T * 0.62), 5.13 / 2, fc="#2a2d33", ec=INK, lw=1.2, ls="--"))
    note(ax3, -12, 31.5, "cable ∅ 5.13 (measured). Exit position NOT yet pinned down —\n"
         "see the questions in the build log (which face, how far from which edge).",
         color=ORANGE, fs=8.5, va="center")

    # ---------------- key numbers ----------------
    fig.text(0.04, 0.115,
             "Key facts for the design:   130 × 40 × 22   |   3 tapped M6 holes per end (1 + 2 pattern), through-tapped, not 2   |   "
             "end blocks 33 mm, so only the outer ≈ 28 mm of each end is bolt-clamped   |   "
             "bending zone ≈ 64 mm   |   cable ∅ 5.13",
             fontsize=10.5, color=INK, fontweight="bold")
    fig.text(0.04, 0.085,
             "Compared with the spec the CAD was built on (130 × 30 × 22, 2 holes per end): the cell is 10 mm wider, "
             "has an extra hole at each end, and shorter clamp blocks. The fit coupon and both halves must be redrawn "
             "before anything is printed.",
             fontsize=10, color=ORANGE)
    out = os.path.join(IMG, "measured_load_cell.png")
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)
    return out


# ======================================================================
# ELECTRONICS
# ======================================================================
def electronics():
    fig = plt.figure(figsize=(17, 7), dpi=140)
    fig.patch.set_facecolor("white")
    fig.suptitle("Electronics — Nano measured with calipers, HX711 still nominal",
                 x=0.04, y=0.955, ha="left", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.04, 0.895, "Blue = measured with calipers (Nano, 2026-10-12).  Grey = reference drawing, not yet measured "
             "(HX711).  Orange = still to measure.", fontsize=10, color=GREY)

    # ---- HX711 ----
    ax = fig.add_axes([0.04, 0.06, 0.30, 0.78])
    clean(ax, (-8, 34), (-8, 30), "HX711 module (small 24 × 16 variant)")
    ax.add_patch(Rectangle((0, 0), 24, 16, fc="#cfe8d5", ec=INK, lw=1.6))
    for i, n in enumerate(["E+", "E−", "A−", "A+", "B−", "B+"]):
        y = 14 - i * 2.4
        ax.add_patch(Circle((2.2, y), 0.7, fc="white", ec=INK))
        note(ax, 3.4, y, n, fs=7.5)
    for i, n in enumerate(["GND", "DT", "SCK", "VCC"]):
        y = 12.5 - i * 2.8
        ax.add_patch(Circle((21.8, y), 0.7, fc="white", ec=INK))
        note(ax, 20.8, y, n, fs=7.5, ha="right")
    for (hx, hy) in ((22.3, 14.5), (22.3, 1.6)):
        ax.add_patch(Circle((hx, hy), 1.0, fc="white", ec=INK))
    dim(ax, (0, 0), (24, 0), "24 ✱", off=-4.5, color=GREY)
    dim(ax, (0, 0), (0, 16), "16 ✱", off=-4.5, color=GREY)
    note(ax, 0, 22, "Real board length, width and thickness:\n____ mm  (to measure; the 24 × 16 is nominal)", color=ORANGE, fs=9)

    # ---- Nano ----
    ax2 = fig.add_axes([0.38, 0.06, 0.34, 0.78])
    clean(ax2, (-8, 52), (-16, 28), "Arduino Nano (clone) — top view")
    ax2.add_patch(Rectangle((0, 0), 44.0, 18.11, fc="#c9d3e6", ec=INK, lw=1.6))
    for i in range(15):
        for y in (1.27, 16.84):
            ax2.add_patch(Circle((3 + i * 2.54, y), 0.5, fc="white", ec=INK, lw=0.6))
    for (hx, hy) in ((1.2, 1.2), (1.2, 16.9), (42.8, 1.2), (42.8, 16.9)):
        ax2.add_patch(Circle((hx, hy), 0.92, fc="white", ec=INK, lw=0.6))
    ax2.add_patch(Rectangle((-1.45, 5.5), 7.0, 6.8, fc="#aeb4be", ec=INK, lw=1.0))
    note(ax2, 8.5, 9, "USB mini-B", fs=8, color=GREY)
    dim(ax2, (0, 0), (44.0, 0), "44.0  board", off=-4.5)
    dim(ax2, (-1.45, 0), (44.0, 0), "46.0  with USB connector", off=-9.5)
    dim(ax2, (44.0, 0), (44.0, 18.11), "18.11", off=5.5)
    note(ax2, 0, 23.5, "USB connector 3.8 above the board.  Pins stick out 8 mm below AND 8 mm above.", color=BLUE, fs=9)
    note(ax2, 0, 21.0, "Clone board: 0.3 mm wider than the reference drawing (18.11 vs 17.78).", color=INK, fs=9)

    # ---- Nano side ----
    ax3 = fig.add_axes([0.76, 0.06, 0.20, 0.78])
    clean(ax3, (-14, 22), (-14, 30), "Nano — side view")
    ax3.add_patch(Rectangle((0, 0), 1.6, 17.78, fc="#c9d3e6", ec=INK, lw=1.2))
    ax3.add_patch(Rectangle((1.6, 5.5), 3.8, 6.8, fc="#aeb4be", ec=INK, lw=1.0))
    for yy in (1.0, 16.6):
        ax3.add_patch(Rectangle((-8.0, yy), 8.0, 0.5, fc=INK, ec=INK))
        ax3.add_patch(Rectangle((1.6, yy), 8.0, 0.5, fc=INK, ec=INK))
    dim(ax3, (-8.0, 0), (0, 0), "8  pins", off=-4)
    dim(ax3, (1.6, 0), (9.6, 0), "8  pins", off=-4)
    dim(ax3, (1.6, 12.3), (5.4, 12.3), "3.8  USB", off=6)
    out = os.path.join(IMG, "measured_electronics.png")
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    for f in (load_cell(), electronics()):
        print("wrote", f)
