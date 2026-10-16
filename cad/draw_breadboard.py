"""draw_breadboard.py — bench test layout: Nano + HX711 on a standard breadboard. Writes images/breadboard_test.png"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

IMG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images"))
INK, GREY = "#1b1f24", "#7a7f87"
COLS = "abcdefghij"
ROWS = 30
P = 1.0                                   # one hole pitch (0.1 in)


def hx(col):                              # x position of a column (gap between e and f)
    i = COLS.index(col)
    return i * P + (1.6 if i >= 5 else 0.0)


def hy(row):                              # row 1 at the top
    return -(row - 1) * P


fig, ax = plt.subplots(figsize=(11, 14), dpi=140)
fig.patch.set_facecolor("white")
ax.set_aspect("equal"); ax.axis("off")
ax.set_xlim(-8.5, 29.5); ax.set_ylim(-31.5, 4.6)

# breadboard body and holes
ax.add_patch(FancyBboxPatch((-1.2, hy(ROWS) - 1.0), hx("j") + 2.4, ROWS * P + 1.0, boxstyle="round,pad=0.2",
                            fc="#f3f1ea", ec="#b9b4a6", lw=1.5))
ax.add_patch(Rectangle((hx("e") + 0.45, hy(ROWS) - 0.8), 0.7, ROWS * P + 0.6, fc="#e2ded2", ec="none"))
for c in COLS:
    ax.text(hx(c), 1.15, c, ha="center", va="center", fontsize=9, color=GREY)
for r in range(1, ROWS + 1):
    ax.text(-1.0, hy(r), str(r), ha="right", va="center", fontsize=7, color=GREY, zorder=6, bbox=dict(boxstyle="square,pad=0.05", fc="#f3f1ea", ec="none"))
    for c in COLS:
        ax.add_patch(Circle((hx(c), hy(r)), 0.16, fc="#9a968c", ec="none"))

# Nano straddling the gap: pins in columns c and h, rows 1..15, USB end at row 1 (off the top edge)
left = ["D12", "D11", "D10", "D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "RST", "RX0", "TX1"]
right = ["D13", "3V3", "REF", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "5V", "RST", "GND", "VIN"]
ax.add_patch(Rectangle((hx("c") - 0.6, hy(15) - 0.6), hx("h") - hx("c") + 1.2, 15 * P + 0.2, fc="#2a5fa8", ec="#0b2f63", lw=1.5, alpha=0.92))
ax.add_patch(Rectangle(((hx("c") + hx("h")) / 2 - 1.3, hy(1) + 0.5), 2.6, 1.6, fc="#c9ccd2", ec=INK, lw=1))
ax.text((hx("c") + hx("h")) / 2, hy(1) + 1.3, "USB", ha="center", va="center", fontsize=8)
used = {"D3", "D2", "GND", "5V"}
for i in range(15):
    r = i + 1
    for col, lab, ha, dx in (("c", left[i], "left", 0.35), ("h", right[i], "right", -0.35)):
        hit = lab in used and not (lab == "GND" and col == "h")
        ax.add_patch(Circle((hx(col), hy(r)), 0.24, fc="#f2c94c" if hit else "#dfe6f2", ec=INK, lw=0.6, zorder=3))
        ax.text(hx(col) + dx, hy(r), lab, ha=ha, va="center", fontsize=7 if not hit else 8,
                color="white", fontweight="bold" if hit else "normal", zorder=3)
ax.text((hx("c") + hx("h")) / 2, hy(8), "Arduino\nNano", ha="center", va="center", fontsize=11, color="white", fontweight="bold")

# HX711 with a 4-pin header in column b, rows 22..25 (board body hangs off the left edge)
HX = [("GND", 22), ("DT", 23), ("SCK", 24), ("VCC", 25)]
ax.add_patch(Rectangle((hx("a") - 7.4, hy(25) - 1.2), 5.4, 5.4, fc="#2e9d5e", ec="#14532d", lw=1.5, alpha=0.95))
ax.text(hx("a") - 6.0, hy(23.5) + 1.9, "HX711", ha="center", va="center", fontsize=10, color="white", fontweight="bold")
for lab, r in HX:
    ax.add_patch(Circle((hx("b"), hy(r)), 0.24, fc="#f2c94c", ec=INK, lw=0.6, zorder=3))
    ax.plot([hx("a") - 2.0, hx("b")], [hy(r), hy(r)], color="#333", lw=2, zorder=2)
    ax.text(hx("a") - 2.8, hy(r), lab, ha="right", va="center", fontsize=8, color="white", fontweight="bold", zorder=3)
for k, (c, w) in enumerate((("#d62828", "red"), ("#111", "black"), ("#2a9d4a", "green"), ("#e8e8e8", "white"))):
    y = hy(22.5) - k * 0.55
    ax.plot([hx("a") - 7.4, hx("a") - 8.2], [y, y], color=c, lw=3, solid_capstyle="round")
ax.text(hx("a") - 5.0, hy(26.6), "to the\nload cell\n(already\nsoldered)", ha="center", va="top", fontsize=7.5, color=GREY)

# jumpers (male-male), drawn as arcs because a real jumper lifts off the board between its two ends
import numpy as np
J = [("GND", 22, ("a", 12), "#111111", "1  GND -> GND", 2.2), ("DT", 23, ("a", 10), "#1f6feb", "2  DT  -> D3", 3.4),
     ("SCK", 24, ("b", 11), "#e07b00", "3  SCK -> D2", 1.2), ("VCC", 25, ("j", 12), "#d62828", "4  VCC -> 5V", 0.0)]
for k, (lab, r, (c2, r2), col, _, bulge) in enumerate(J):
    p0, p2 = np.array([hx("d"), hy(r)]), np.array([hx(c2), hy(r2)])
    if c2 == "j":
        ctrl = [p0, np.array([19.0, hy(r)]), np.array([19.0, hy(r2)]), p2]
        t = np.linspace(0, 1, 60)[:, None]
        pts = ((1 - t) ** 3) * ctrl[0] + 3 * ((1 - t) ** 2) * t * ctrl[1] + 3 * (1 - t) * t ** 2 * ctrl[2] + t ** 3 * ctrl[3]
    else:
        mid = (p0 + p2) / 2 + np.array([-bulge, 0.0])
        t = np.linspace(0, 1, 60)[:, None]
        pts = ((1 - t) ** 2) * p0 + 2 * (1 - t) * t * mid + t ** 2 * p2
    ax.plot(pts[:, 0], pts[:, 1], color="#222", lw=4.6, solid_capstyle="round", zorder=4)
    ax.plot(pts[:, 0], pts[:, 1], color=col, lw=3.0, solid_capstyle="round", zorder=4.1)
    for (xx, yy) in (p0, p2):
        ax.add_patch(Circle((xx, yy), 0.33, fc=col, ec="#222", lw=1, zorder=5))
        ax.text(xx, yy, str(k + 1), ha="center", va="center", fontsize=6.5, color="white" if col != "#e8e8e8" else INK,
                fontweight="bold", zorder=6)

# legend
lx, ly = 19.9, hy(17)
ax.text(lx, ly, "4 jumper wires (male-male)", fontsize=10, fontweight="bold", color=INK)
for i, (_, _, _, col, txt, _b) in enumerate(J):
    ax.plot([lx, lx + 0.9], [ly - 0.9 - i * 0.75] * 2, color=col, lw=3.5, solid_capstyle="round")
    ax.text(lx + 1.2, ly - 0.9 - i * 0.75, txt, va="center", fontsize=9, color=INK, family="monospace")

ax.text(-8.3, 4.1, "Bench test: HX711 to Arduino Nano on a breadboard", fontsize=14, fontweight="bold", color=INK)
ax.text(-8.3, 3.2, "Each numbered row of 5 holes (a-e, or f-j) is one connected strip. Row numbers are an example;"
        " the pin LABELS printed on your boards are what count.", fontsize=8, color=GREY)
os.makedirs(IMG, exist_ok=True)
out = os.path.join(IMG, "breadboard_test.png")
fig.savefig(out, dpi=140, facecolor="white", bbox_inches="tight")
print("wrote", out)
