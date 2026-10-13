"""Draws the electronics bay (top view + side section) from the same constants as dynamometer_cad.py."""
import os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dynamometer_cad.py")).read()
ns = {}
exec(src[src.index("CT, CW, CL"):src.index("OUT = os.path")].replace("import cadquery as cq", ""), {"__builtins__": __builtins__}, ns) if False else None
import dynamometer_cad as D   # constants only (module guards its main block)

fig, (a, b) = plt.subplots(1, 2, figsize=(15, 8.2), gridspec_kw={"width_ratios": [1, 1.05]})
AX = D.AX
# ---------------- top view (looking up from below, cover removed) ----------------
a.set_aspect("equal"); a.set_title("TOP VIEW  -  looking into the bay from below (cover removed), z = -44 .. -7", fontsize=11)
a.add_patch(Circle((AX, 0), 29.0, fc="#dfe3e8", ec="#555", lw=1.2))
a.add_patch(Circle((AX, 0), D.POD_BORE, fc="white", ec="#222", lw=2))
a.text(AX, 27.0, "bore  ∅ 50", ha="center", fontsize=9)
# nano
nx0 = AX - D.NANO_W/2
a.add_patch(Rectangle((nx0, -22), D.NANO_W, 44, fc="#2a7fb8", ec="#0b3f63", alpha=.55, lw=1.5))
a.add_patch(Rectangle((AX-3.9, -24), 7.8, 6, fc="#bbb", ec="#333"))
for sx in (-1, 1): a.plot([AX+sx*D.NANO_ROW/2]*2, [-19, 19], "k.", ms=1.5); a.plot([AX+sx*D.NANO_ROW/2]*2, [-19, 19], color="#c33", lw=3, alpha=.5)
a.text(AX, 2, "Arduino Nano\n44 x 18.11\n(USB end at the bottom)", ha="center", va="center", fontsize=9, color="#07304d")
# rail and stops
a.add_patch(Rectangle((AX-5, -21), 10, 42, fc="none", ec="#d77", lw=1.2, ls="--"))
a.text(AX+5.4, 14, "central rail 10 wide\n+ foam tape", fontsize=8, color="#a33")
for sx in (-1, 1):
    for yy in (-12, 12):
        x0 = AX + sx*(D.NANO_W/2+0.4)
        a.add_patch(Rectangle((min(x0, x0+sx*1.4), yy-1.5), 1.4, 3, fc="#e8a", ec="#a35"))
# hx711
a.add_patch(Rectangle((D.HX_XC-D.HX_T/2, -8), D.HX_T, 16, fc="#2e9d5e", ec="#14532d", lw=1.5))
for sx in (-1, 1):
    xin = D.HX_XC + sx*D.HX_SLOT/2
    a.add_patch(Rectangle((min(xin, xin+sx*1.2), -5), 1.2, 10, fc="#e8a", ec="#a35"))
a.text(D.HX_XC, -11, "HX711 on edge\n(24 tall, 16 across)\nNOMINAL size", ha="center", va="top", fontsize=8, color="#14532d")
# bosses
for bx, by in D.BOSSES:
    a.add_patch(Circle((bx, by), D.BOSS_R, fc="#bbb", ec="#222")); a.add_patch(Circle((bx, by), 1.4, fc="white", ec="#222"))
    a.text(bx, by-5.2, "M3 boss", ha="center", fontsize=8)
# eyelet
a.add_patch(Rectangle((D.EYE[0]-5, 17.5), 10, 9, fc="#bbb", ec="#222"))
a.add_patch(Circle(D.EYE, 2.3, fc="white", ec="#c00", lw=1.5))
a.annotate("wire eyelet ∅4.6\n(cell wires drop in here)", D.EYE, (AX-24, 31), fontsize=8.5, arrowprops=dict(arrowstyle="->"))
# window
a.add_patch(Rectangle((AX-7, -29.5), 14, 6, fc="#ffd", ec="#aa0", lw=1.5, ls="--"))
a.text(AX, -33, "USB window 14 wide", ha="center", fontsize=9, color="#770")
a.set_xlim(AX-38, AX+38); a.set_ylim(-37, 37); a.set_xlabel("x  (palm side is left, finger side is right)  mm"); a.set_ylabel("y  mm")
a.grid(alpha=.25)

# ---------------- side section x = AX (y across, z up) ----------------
b.set_title("SIDE SECTION  -  cut through the grip axis, z from the cover up to the cell's lower end", fontsize=11)
b.set_aspect("equal")
Zc = D.Z_COVER
b.add_patch(Rectangle((-29, Zc-4), 58, 4, fc="#999", ec="#222")); b.text(0, Zc-2.6, "cover (4 mm)", ha="center", fontsize=8, color="white")
for s in (-1, 1): b.add_patch(Rectangle((s*25 if s > 0 else -29, Zc), 4 if s > 0 else 4, D.Z_POD_TOP-Zc, fc="#dfe3e8", ec="#222"))
b.add_patch(Rectangle((-5, Zc), 10, D.RAIL_H, fc="#e8a", ec="#a35")); b.text(0, Zc+4, "rail", ha="center", fontsize=8)
b.add_patch(Rectangle((-22, D.PCB_BOT), 44, D.PCB_T, fc="#2a7fb8", ec="#0b3f63"))
b.add_patch(Rectangle((-24, D.PCB_TOP), 6, D.NANO_USB_H, fc="#bbb", ec="#333")); b.text(-27, D.USB_ZC, "USB", fontsize=8, ha="right")
b.add_patch(Rectangle((-19.5, D.PCB_BOT-D.NANO_PIN), 39, D.NANO_PIN, fc="#c33", alpha=.25, ec="#a22")); b.text(0, D.PCB_BOT-4.3, "lower pins (8 mm)", ha="center", fontsize=8, color="#a22")
b.add_patch(Rectangle((-19.5, D.PCB_TOP), 39, D.NANO_PIN, fc="#c33", alpha=.25, ec="#a22")); b.text(0, D.PCB_TOP+4.0, "upper pins (8 mm) - solder wires here", ha="center", fontsize=8, color="#a22")
b.add_patch(Rectangle((-30.0, D.USB_ZC-D.WIN_H/2), 5.0, D.WIN_H, fc="#ffd", ec="#aa0", ls="--")); b.text(-27.6, D.USB_ZC+D.WIN_H/2+1.2, "window", fontsize=8, ha="center", color="#770")
b.add_patch(Rectangle((-28, D.USB_ZC-4), -0.1, 8, fc="none"))
b.add_patch(Rectangle((-46, D.USB_ZC-4), 22, 8, fc="#333", alpha=.25, ec="#333")); b.text(-35, D.USB_ZC-6.5, "plug", fontsize=8, ha="center")
# eyelet + wire
b.add_patch(Rectangle((17.5, -17), 9, 8, fc="#bbb", ec="#222")); b.add_patch(Rectangle((D.EYE[1]-2.3, -17), 4.6, 8, fc="white", ec="#c00"))
b.plot([D.EYE[1]]*2, [-9, 5.6], color="#c00", lw=3); b.text(D.EYE[1]+3, -2, "cell wires\n(jacket trimmed)", fontsize=8.5, color="#c00")
b.add_patch(Rectangle((-20, 0), 40, 14, fc="#2e9d9d", alpha=.35, ec="#1b6b6b")); b.text(0, 7, "load cell, lower end block\n(cable exits +y face at z = 5.6)", ha="center", fontsize=8.5)
b.plot([20, 22.1], [5.6, 5.6], color="#c00", lw=3)
b.add_patch(Rectangle((-26, D.Z_POD_TOP), 52, 0.3, fc="#555"))
b.set_xlim(-50, 33); b.set_ylim(Zc-7, 17); b.set_xlabel("y  mm  (USB end on the left)"); b.set_ylabel("z  mm"); b.grid(alpha=.25)
b.axhline(Zc, color="#222", lw=.8)
fig.suptitle("Electronics bay  -  P1 round ∅ 50 bore, R1 trimmed jacket + eyelet.   Blue/green/red are placeholders sized from caliper data (Nano measured; HX711 nominal).", fontsize=11, y=0.995)
plt.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "pod_layout.png")
plt.savefig(out, dpi=140); print(os.path.abspath(out))
