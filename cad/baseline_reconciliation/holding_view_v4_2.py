"""
holding_view_v4_2.py - Annotated holding view of the Jamar v4.2 candidate, drawn from its exported
assembly STEP (actual geometry), for review BEFORE any grip change.  [GEOMETRIC-ONLY]

Solid fills are true sections of the exported parts. The amber dashed hand is ILLUSTRATIVE ONLY:
it is not CAD, not fitted to anyone's hand, and proves nothing about comfort or fit.

Usage (needs cadquery, shapely, matplotlib):
    python holding_view_v4_2.py ../jamar_v4_2_review/output/jamar_v4_2_review_assembly.step out.png
"""
import sys

import cadquery as cq
import matplotlib
import numpy as np
from shapely.geometry import Polygon

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

STEP, OUT = sys.argv[1], sys.argv[2]
NAMES = ["frame", "palm bar", "finger part", "pod cover", "guard", "load cell"]
COLORS = {"frame": "#cfd5de", "palm bar": "#3a78c2", "finger part": "#252b36", "pod cover": "#8d97a8",
          "guard": "#8d97a8", "load cell": "#21a585"}
GREEN, BLUE, RED, AMBER = "#0f7a55", "#1d4ed8", "#9b1c1c", "#8a5a12"

solids = cq.importers.importStep(STEP).solids().vals()
assert len(solids) == 6, f"expected 6 solids, got {len(solids)}"


def _wire_xy(wire, axes, n=240):
    pts = [wire.positionAt(t) for t in np.linspace(0, 1, n)]
    return [(p.toTuple()[axes[0]], p.toTuple()[axes[1]]) for p in pts]


def section(solid, origin, normal, axes):
    """Exact planar B-rep section of a solid, as a shapely shape with holes."""
    plane = cq.Face.makePlane(600, 600, cq.Vector(*origin), cq.Vector(*normal))
    cut = solid.intersect(plane)
    shape = None
    for f in cut.Faces():
        outer = _wire_xy(f.outerWire(), axes)
        holes = [_wire_xy(w, axes) for w in f.innerWires()]
        p = Polygon(outer, holes).buffer(0)
        shape = p if shape is None else shape.union(p)
    return shape


def fill(ax, shape, color, edge="#1d2430"):
    if shape is None:
        return
    for g in getattr(shape, "geoms", [shape]):
        if g.is_empty:
            continue
        xs, ys = g.exterior.xy
        ax.fill(xs, ys, color=color, ec=edge, lw=0.8, zorder=3)
        for h in g.interiors:
            hx, hy = h.xy
            ax.fill(hx, hy, color="#f7f8fa", ec=edge, lw=0.6, zorder=4)


def arrow(ax, a, b, color, scale=22, lw=2.5):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=scale, color=color, lw=lw, zorder=7))


fig = plt.figure(figsize=(19, 10.5))
fig.suptitle("Jamar v4.2 candidate: annotated holding view from the exported assembly STEP   [GEOMETRIC-ONLY]",
             fontsize=15, fontweight="bold", y=0.985)
fig.text(0.5, 0.945, "Solid fills = true sections of exported parts (default palm setting).  Amber dashed hand = ILLUSTRATIVE, "
         "not CAD, not fitted to any hand.  Not assembled, not load-tested, not calibrated.",
         ha="center", fontsize=10.5, color="#555")

# ---------- A: side section at y = 0 (x horizontal, z vertical) ----------
axA = fig.add_axes([0.04, 0.07, 0.47, 0.84])
for name, m in zip(NAMES, solids):
    fill(axA, section(m, [0, 0, 0], [0, 1, 0], [0, 2]), COLORS[name])
axA.set_title("A. Side section at y = 0: what each surface does", fontsize=12, fontweight="bold")
palm = np.array([[-140, 8], [-118, -2], [-96, 4], [-84, 10], [-84, 100], [-96, 112], [-122, 116], [-140, 100]])
axA.fill(palm[:, 0], palm[:, 1], fc="#f6d9a6", ec="#d79b3c", ls="--", lw=1.6, alpha=0.55, zorder=2)
axA.text(-118, 58, "ILLUSTRATIVE\nPALM\n(not CAD)", ha="center", fontsize=9, color=AMBER, fontweight="bold", zorder=6)
for z0, lab in [(4, "little"), (26, "ring"), (48, "middle"), (70, "index")]:
    axA.add_patch(plt.Rectangle((-27.4, z0 + 1), 20.5, 19, fc="#bfe9d8", ec="#2c9a6f", ls="--", lw=1, alpha=0.6, zorder=2))
    axA.text(-17, z0 + 10.5, lab, ha="center", va="center", fontsize=7.5, color="#1f6e4f", zorder=6)
arrow(axA, (-128, 40), (-86, 40), BLUE)
axA.text(-140, 30, "1  PALM pushes +x on the\n   palm bar's outer face", fontsize=9, color=BLUE, fontweight="bold", zorder=7)
arrow(axA, (-8, 28), (-25.5, 28), GREEN)
axA.text(-140, -24, "2  FOUR FINGERS pull -x on the finger bar's back face\n   (they wrap round the guard side: see B)",
         fontsize=9, color=GREEN, fontweight="bold", zorder=7)
axA.annotate("", xy=(-27.5, 147), xytext=(-82.0, 147), arrowprops=dict(arrowstyle="<->", color="#111", lw=1.4))
axA.text(-54.7, 150, "grip span 54.0-54.5 mm at z = 40-90 (measured)", ha="center", fontsize=8.5)
axA.annotate("", xy=(-6.0, -40), xytext=(-27.5, -40), arrowprops=dict(arrowstyle="<->", color="#111", lw=1.2))
axA.text(-16.7, -48, "fingertip pocket\n21.5 mm", ha="center", fontsize=8.5)
axA.annotate("", xy=(-33, 92), xytext=(-33, 3.5), arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.2))
axA.text(-36, 47, "finger window\n~88 mm\n(z 3.5-92)", ha="right", fontsize=8.5, color=GREEN)
axA.text(-22, 118, "3  finger-part bracket\n   (fingers must stay below z ~ 92)", fontsize=8.5, color="#333", zorder=7,
         bbox=dict(fc="white", ec="#999", lw=0.6, alpha=0.92, boxstyle="round,pad=0.25"))
axA.text(36, -30, "4  NOT A GRIP\nload cell +\nNano/HX711 housing", ha="center", fontsize=9, color=RED, fontweight="bold", zorder=7)
axA.text(-55, 160, "5  keyed palm seat: the bar moves 0.35 mm in +x, then bears on frame PETG (measured)",
         fontsize=8.5, color=BLUE, ha="center")
axA.set_xlabel("x (mm):  palm bar  ->  finger bar  ->  load cell / electronics", fontsize=10)
axA.set_ylabel("z (mm)", fontsize=10)
axA.set_aspect("equal")
axA.grid(alpha=0.25)
axA.set_xlim(-145, 60)
axA.set_ylim(-62, 168)

# ---------- B: top-down slice at z = 50 (x horizontal, y vertical) ----------
axB = fig.add_axes([0.55, 0.40, 0.43, 0.50])
for name, m in zip(NAMES, solids):
    fill(axB, section(m, [0, 0, 50], [0, 0, 1], [0, 1]), COLORS[name])
hand = np.array([[-140, 22], [-112, 30], [-86, 24], [-84, -16], [-80, -24], [-30, -24], [-8, -18], [-6, -6],
                 [-10, 4], [-26, 6], [-28, -14], [-34, -32], [-80, -36], [-112, -34], [-140, -24]])
axB.fill(hand[:, 0], hand[:, 1], fc="#f6d9a6", ec="#d79b3c", ls="--", lw=1.6, alpha=0.5, zorder=2)
axB.text(-120, -2, "ILLUSTRATIVE\nhand (not CAD)", ha="center", fontsize=9, color=AMBER, fontweight="bold", zorder=6)
arrow(axB, (-112, 8), (-85, 8), BLUE, scale=20, lw=2.3)
arrow(axB, (-9, -2), (-26, -2), GREEN, scale=20, lw=2.3)
axB.text(-55, -46, "fingers wrap round the -y (guard) side of both bars;\n"
         "fingertips curl into the 21.5 mm pocket behind the finger bar",
         ha="center", fontsize=9, color=GREEN)
axB.text(20, 46, "NOT A GRIP (pod + guard)", ha="center", fontsize=9, color=RED, fontweight="bold")
axB.set_title("B. Top-down slice at z = 50 mm (middle-finger height)", fontsize=12, fontweight="bold")
axB.set_xlabel("x (mm)")
axB.set_ylabel("y (mm)")
axB.set_aspect("equal")
axB.grid(alpha=0.25)
axB.set_xlim(-145, 60)
axB.set_ylim(-54, 56)

# ---------- C: what is measured, what is not ----------
axC = fig.add_axes([0.55, 0.05, 0.43, 0.30])
axC.axis("off")
notes = [
    "Measured from the exported assembly STEP [GEOMETRIC-ONLY]:",
    " - Palm bar free travel before bearing on the frame: 0.35 mm each way (keyed shoulder exists).",
    " - Finger part travel along the squeeze axis before touching anything: 17.1 mm (no bypass on that axis).",
    " - Grip span, palm face to finger pull face: 54.0-54.5 mm (v4.2 notes say 56.0).",
    "Uncertain - needs your input before any grip change:",
    " - Hand breadth across the four knuckles: the finger window is ~88 mm; large hands may not fit.",
    " - Fingertip thickness vs the 21.5 mm pocket; comfortable span for your hand at setting 2.",
    " - Real cable length (v4.2 assumes ~8 cm; repo docs say ~1 m, never measured). Decides the bay.",
    "Not shown or proven: PETG seat/arm strength, printed fit, comfort, calibration, safe load.",
]
for i, t in enumerate(notes):
    head = not t.startswith(" ")
    axC.text(0, 1 - i * 0.11, t, fontsize=9.6, va="top", fontweight="bold" if head else "normal",
             color=RED if t.startswith(("Uncertain", "Not shown")) else "#111")

fig.savefig(OUT, dpi=150)
print("wrote", OUT)
