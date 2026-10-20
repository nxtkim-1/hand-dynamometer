"""draw_wiring.py — wiring diagram. Writes ../images/drawing_wiring.png"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
os.makedirs(IMG, exist_ok=True)
fig, ax = plt.subplots(figsize=(11, 5.6))

def box(x, y, w, h, label, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.25",
                                fc=fc, ec="k", lw=1.1))
    ax.text(x + w/2, y + h - 0.42, label, ha="center", va="top", fontsize=10, fontweight="bold")

box(0.3, 1.2, 2.3, 3.4, "TAL220\n100 kg cell", "#2f9e8a")
box(4.3, 1.2, 2.4, 3.4, "HX711", "#c9cbd2")
box(8.3, 1.2, 2.4, 3.4, "Arduino Nano", "#c9cbd2")

cell = [("red",   "E+",  4.05, "#cc3333"),
        ("black", "E\u2212", 3.30, "#222222"),
        ("green", "A+ (O+)", 2.55, "#2e8b2e"),
        ("white", "A\u2212 (O\u2212)", 1.80, "#888888")]
for name, pad, y, col in cell:
    ax.plot([2.6, 4.3], [y, y], color=col, lw=2.4,
            solid_capstyle="round", zorder=2)
    ax.text(3.45, y - 0.34, name, ha="center", fontsize=8.5, color=col if col != "#888888" else "#555")
    ax.text(4.40, y+0.16, pad, ha="left", va="bottom", fontsize=9)

mcu = [("VCC", "5V", 4.05, "#cc3333"), ("GND", "GND", 3.30, "#222222"),
       ("DT", "D3", 2.55, "#3050c0"), ("SCK", "D2", 1.80, "#c08030")]
for pad, pin, y, col in mcu:
    ax.plot([6.7, 8.3], [y, y], color=col, lw=2.4, solid_capstyle="round", zorder=2)
    ax.text(6.55, y+0.16, pad, ha="right", va="bottom", fontsize=9)
    ax.text(8.42, y+0.16, pin, ha="left", va="bottom", fontsize=9)

ax.annotate("", (10.7, 2.9), (12.0, 2.9), arrowprops=dict(arrowstyle="<->", lw=1.4))
ax.text(11.35, 3.08, "USB", ha="center", fontsize=9)
ax.text(11.35, 2.66, "115200 baud", ha="center", fontsize=8, color="#555")

ax.text(0.3, 0.55, "Solder the four cell wires to the HX711 pads. Zip-tie the bundle 30 mm from the cell "
                   "as strain relief —\nthese wires always break at the joint. Check colours against the "
                   "label on your own cell before soldering.",
        fontsize=8.5, va="top", color="#333")
ax.text(0.3, 5.05, "Wiring — four wires in, four wires out. That is the entire circuit.",
        fontsize=11, fontweight="bold")

ax.set_xlim(0, 12.4); ax.set_ylim(0, 5.4); ax.axis("off")
fig.tight_layout(); fig.savefig(os.path.join(IMG, "drawing_wiring.png"), dpi=150)
print("wrote drawing_wiring.png")
