"""draw_jumper_wiring.py — build-day sheet for the v3 compact box with Dupont jumper wires.
Writes images/wiring_jumpers_v3.png.   Run:  python draw_jumper_wiring.py   (needs matplotlib; reads compact_base_draft for positions)

Panel A: which HX711 pad goes to which Nano pin (same pins as the firmware: DT -> D3, SCK -> D2).
Panel B: how to put a jumper wire into an HX711 hole (cut, strip, tin, solder from the back).
Panel C: where the boards sit in the closed box, drawn to scale from the CAD, seen through the open bottom.

Nano drawn components up with the USB end on the LEFT. Its two pin rows, from the USB end:
  far row  : D12 D11 D10 D9 D8 D7 D6 D5 D4 D3 D2 GND RST RX0 TX1
  wall row : D13 3V3 REF A0 A1 A2 A3 A4 A5 A6 A7 5V RST GND VIN
(always confirm against the labels printed on YOUR board)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon

import compact_base_draft as C
import dynamometer_cad as D

IMG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images"))
INK, GREY, LIGHT = "#1b1f24", "#6b7079", "#eef0f3"
PCB_BLUE, HX_GREEN, PAD = "#2f5f9e", "#cfe8d5", "#e8c76a"
JUMP = {"VCC": ("#d62828", "red"), "GND": ("#111111", "black"), "DT": ("#e0a400", "yellow"), "SCK": ("#2a6fd6", "blue")}
NANO_PIN = {"VCC": "5V", "GND": "GND", "DT": "D3", "SCK": "D2"}

FAR = ["D12", "D11", "D10", "D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "RST", "RX0", "TX1"]
WALL = ["D13", "3V3", "REF", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "5V", "RST", "GND", "VIN"]
USED = {"D3", "D2", "5V"}

fig = plt.figure(figsize=(18, 13), dpi=130)
fig.patch.set_facecolor("white")
fig.text(0.03, 0.968, "Build day: HX711 → Nano with Dupont jumper wires (v3 compact box)", fontsize=19, fontweight="bold", color=INK)
fig.text(0.03, 0.925, "Load cell → HX711 is already soldered. Today: 4 jumpers. The female end clips onto the Nano's pins;\n"
         "the other end is soldered into the HX711. Check every label against the text printed on YOUR boards.", fontsize=10.5, color=GREY)

# =====================================================================  A: wiring
ax = fig.add_axes([0.02, 0.42, 0.62, 0.47]); ax.set_xlim(-6, 112); ax.set_ylim(-46, 30); ax.set_aspect("equal"); ax.axis("off")
ax.text(-5, 28, "A   Wiring — 4 jumpers", fontsize=14, fontweight="bold", color=INK)

# Nano (schematic, not to scale): USB left
nx0, ny0, nw, nh = 30, 0, 66, 20
ax.add_patch(FancyBboxPatch((nx0, ny0), nw, nh, boxstyle="round,pad=0.4", fc=PCB_BLUE, ec=INK, lw=1.6, zorder=2))
ax.add_patch(Rectangle((nx0 - 4.5, ny0 + 6.5), 6, 7, fc="#c9ccd1", ec=INK, lw=1.2, zorder=3))
ax.text(nx0 - 5.5, ny0 + 10, "micro-USB", ha="right", va="center", fontsize=9, color=GREY)
ax.text(nx0 + nw / 2, ny0 + nh / 2, "Arduino Nano (components up)", ha="center", va="center", fontsize=9.5, color="white", fontweight="bold", zorder=3)
pitch = (nw - 8) / 14


def pin_xy(name, row):
    lst = FAR if row == "far" else WALL
    i = lst.index(name)
    return nx0 + 4 + i * pitch, (ny0 + nh - 2.2) if row == "far" else (ny0 + 2.2)


for row, lst in (("far", FAR), ("wall", WALL)):
    for n in lst:
        x, y = pin_xy(n, row)
        used = (n in USED) or (n == "GND" and row == "far")
        ax.add_patch(Rectangle((x - 0.9, y - 0.9), 1.8, 1.8, fc=PAD if used else "#9aa3ad", ec=INK, lw=0.8, zorder=4))
        ty = y - 1.5 if row == "far" else y + 1.5
        ax.text(x, ty, n, ha="center", va="top" if row == "far" else "bottom", fontsize=8.4 if used else 6.4, rotation=90,
                color=PAD if used else "#c9d3e0", fontweight="bold" if used else "normal", zorder=4)
ax.text(nx0 - 1.5, ny0 + nh - 1.5, "far row", fontsize=8.5, color=GREY, va="center", ha="right")
ax.text(nx0 - 1.5, ny0 + 1.5, "wall row", fontsize=8.5, color=GREY, va="center", ha="right")

# HX711 below the Nano (it sits on the wall below the Nano's 'wall row' in the box)
hx0, hy0, hw, hh = 44, -40, 30, 20
ax.add_patch(Rectangle((hx0, hy0), hw, hh, fc=HX_GREEN, ec=INK, lw=1.6, zorder=2))
ax.text(hx0 + hw / 2 - 2, hy0 + hh / 2, "HX711", ha="center", va="center", fontsize=12, fontweight="bold", color=INK, zorder=3)
inp = ["E+", "E−", "A−", "A+", "B−", "B+"]
for i, n in enumerate(inp):
    y = hy0 + hh - 2.5 - i * 3.0
    ax.add_patch(Circle((hx0 + 2.2, y), 0.9, fc=PAD, ec=INK, zorder=3))
    ax.text(hx0 + 3.8, y, n, fontsize=7.5, va="center", color=INK if i < 4 else GREY, zorder=3)
cell_cols = ["#d62828", "#111111", "#f4f4f4", "#2a9d4a"]
for i, c in enumerate(cell_cols):
    y = hy0 + hh - 2.5 - i * 3.0
    ax.plot([hx0 - 9, hx0 + 2.2], [y, y], color=INK, lw=4.2, solid_capstyle="round", zorder=1)
    ax.plot([hx0 - 9, hx0 + 2.2], [y, y], color=c, lw=2.8, solid_capstyle="round", zorder=1.1)
ax.text(hx0 - 4, hy0 + hh + 1.5, "load cell wires\n(already soldered)", ha="center", va="bottom", fontsize=8.5, color=GREY)

out = ["GND", "DT", "SCK", "VCC"]
hx_pad = {}
for i, n in enumerate(out):
    y = hy0 + hh - 4 - i * 4.0
    x = hx0 + hw - 2.4
    hx_pad[n] = (x, y)
    ax.add_patch(Circle((x, y), 1.0, fc=PAD, ec=INK, zorder=3))
    ax.text(x - 2.0, y, n, fontsize=9.5, va="center", ha="right", color=INK, fontweight="bold", zorder=3)

# jumper routes: out of the HX711's right edge, right, then up to the pin
lanes = {"GND": 108, "DT": 100, "SCK": 104, "VCC": 85}
for n in out:
    col, cname = JUMP[n]
    sx, sy = hx_pad[n]
    if n == "VCC":
        tx, ty = pin_xy("5V", "wall"); ty -= 0.9
        path = [(sx, sy), (lanes[n] - 6, sy), (lanes[n] - 6, -12), (tx, -12), (tx, ty)]
    else:
        row_pin = "GND" if n == "GND" else NANO_PIN[n]
        tx, ty = pin_xy(row_pin, "far"); ty += 0.9
        top = 27 + {"GND": 0, "SCK": -1.6, "DT": -3.2}[n]
        path = [(sx, sy), (lanes[n], sy), (lanes[n], top), (tx, top), (tx, ty)]
    xs, ys = zip(*path)
    ax.plot(xs, ys, color=INK, lw=4.6, solid_joinstyle="round", solid_capstyle="round", zorder=5)
    ax.plot(xs, ys, color=col if n != "GND" else "#3a3a3a", lw=3.1, solid_joinstyle="round", solid_capstyle="round", zorder=5.1)
    # female housing at the Nano end
    hb = ty if n != "VCC" else ty - 3.2              # housing sits on the pin, wire leaves away from the board
    ax.add_patch(Rectangle((tx - 1.1, hb), 2.2, 3.2, fc="#2b2b2b", ec="white", lw=0.6, zorder=6))
# solder dots at the HX711 end
for n in out:
    ax.add_patch(Circle(hx_pad[n], 1.3, fc="#c0c4c9", ec=INK, lw=1.0, zorder=6))
ax.text(hx0 + hw + 1, hy0 - 2.5, "soldered here (B)", fontsize=8.5, color=GREY, ha="center")
ax.text(70, 26.6, "female ends clip onto the pins", fontsize=8.5, color=GREY, ha="right")

# connection table
rows = [("HX711", "jumper", "Nano pin")] + [
    ("VCC", "red", "5V"), ("GND", "black", "GND (next to D2)"), ("DT", "yellow", "D3"), ("SCK", "blue", "D2")]
tx0, ty0 = -5, -14
cw = [7, 8, 0]
for r, row in enumerate(rows):
    x = tx0
    for c, cell in enumerate(row):
        bold = r == 0 or c in (0, 2)
        colr = INK
        if r > 0 and c == 1:
            colr = JUMP[row[0]][0] if row[0] != "GND" else INK
        ax.text(x, ty0 - r * 4.4, cell, fontsize=9.5 if r else 8.8, color=colr if r else GREY, fontweight="bold" if bold else "normal", va="center")
        x += cw[c] if c < 2 else 0
    if r == 0:
        ax.plot([tx0, tx0 + 30], [ty0 - 2.2, ty0 - 2.2], color=GREY, lw=0.8)
ax.text(tx0, ty0 - 5 * 4.4 - 1, "Same pins as the firmware\n(DT = D3, SCK = D2).\nColours are only a suggestion:\nwrite yours in the build log.", fontsize=8.8, color=GREY, va="top")

# =====================================================================  B: jumper into HX711
bx = fig.add_axes([0.02, 0.03, 0.58, 0.37]); bx.set_xlim(0, 120); bx.set_ylim(-4, 50); bx.set_aspect("equal"); bx.axis("off")
bx.text(1, 48, "B   One jumper into the HX711 (repeat ×4)", fontsize=14, fontweight="bold", color=INK)
steps = [
    ("1  Cut", "Keep the female end.\nCut 10 cm from it\n(20 cm wires: cut, keep 10 cm)."),
    ("2  Strip 3 mm", "Twist the strands\ntight."),
    ("3  Tin", "Iron on the wire,\nfeed a little solder\nuntil it's silver."),
    ("4  Push through", "From the FRONT\n(labelled side) into\nthe hole, out the back."),
    ("5  Solder at the back", "Iron on pad + wire\n2 s, feed solder.\nShiny cone. Trim.")]
for i, (title, txt) in enumerate(steps):
    x0 = 2 + i * 23.6
    bx.add_patch(FancyBboxPatch((x0, 0), 21.5, 41, boxstyle="round,pad=0.4", fc=LIGHT, ec="#c8ccd2", lw=1))
    bx.text(x0 + 1, 39, title, fontsize=10.5, fontweight="bold", color=INK, va="top")
    bx.text(x0 + 1, 11.5, txt, fontsize=8.5, color=GREY, va="top")
    cy = 24
    if i == 0:
        bx.add_patch(Rectangle((x0 + 1.5, cy - 1.6), 4.5, 3.2, fc="#2b2b2b", ec=INK))
        bx.plot([x0 + 6, x0 + 20], [cy, cy], color=INK, lw=4.4); bx.plot([x0 + 6, x0 + 20], [cy, cy], color="#e0a400", lw=3)
        bx.plot([x0 + 15, x0 + 15], [cy - 5, cy + 5], color="#c0392b", lw=1.5, ls="--")
        bx.text(x0 + 15, cy + 6, "cut", ha="center", fontsize=8.5, color="#c0392b")
        bx.annotate("", xy=(x0 + 6, cy - 4), xytext=(x0 + 15, cy - 4), arrowprops=dict(arrowstyle="<->", color=GREY, lw=0.9))
        bx.text(x0 + 10.5, cy - 6.5, "10 cm", ha="center", fontsize=8, color=GREY)
    elif i in (1, 2):
        bx.plot([x0 + 2, x0 + 13], [cy, cy], color=INK, lw=4.4); bx.plot([x0 + 2, x0 + 13], [cy, cy], color="#e0a400", lw=3)
        bx.plot([x0 + 13, x0 + 17], [cy, cy], color=("#b87333" if i == 1 else "#b8bcc2"), lw=2.2, solid_capstyle="butt")
        bx.annotate("", xy=(x0 + 13, cy + 3.5), xytext=(x0 + 17, cy + 3.5), arrowprops=dict(arrowstyle="<->", color=GREY, lw=0.9))
        bx.text(x0 + 15, cy + 4.5, "3 mm", ha="center", fontsize=8, color=GREY)
    else:
        # side view of the board: front face at top
        bx.add_patch(Rectangle((x0 + 3, cy - 1), 15, 2, fc=HX_GREEN, ec=INK))
        bx.text(x0 + 3.2, cy + 1.4, "front (labels)", fontsize=7, color=GREY)
        bx.text(x0 + 3.2, cy - 3.0, "back", fontsize=7, color=GREY, va="top")
        bx.plot([x0 + 10.5, x0 + 10.5], [cy + 9, cy + 1], color=INK, lw=4.4); bx.plot([x0 + 10.5, x0 + 10.5], [cy + 9, cy + 1], color="#e0a400", lw=3)
        bx.plot([x0 + 10.5, x0 + 10.5], [cy + 1, cy - (2.5 if i == 3 else 1.6)], color="#b8bcc2", lw=2.2)
        if i == 4:
            bx.add_patch(Polygon([(x0 + 8.3, cy - 1), (x0 + 12.7, cy - 1), (x0 + 10.5, cy - 3.2)], fc="#c0c4c9", ec=INK, lw=0.9))
            bx.text(x0 + 13.5, cy - 3.0, "cone", fontsize=7.5, color=GREY, va="center")
bx.text(2, -3, "Iron about 330 °C for leaded solder, 350–370 °C for lead-free. No solder may bridge two pads. "
        "When all 4 are done: a blob of hot glue over the 4 joints on the back (strain relief).", fontsize=9, color=GREY)

# =====================================================================  C: box layout, to scale from the CAD
cx = fig.add_axes([0.64, 0.05, 0.34, 0.80])
cx.set_aspect("equal"); cx.axis("off")
cx.text(0.0, 1.02, "C   Where it sits (to scale, closed box,\n     looking in through the open bottom)", transform=cx.transAxes, fontsize=14, fontweight="bold", color=INK, va="bottom")
F = lambda x: -x                                   # seen from below: mirror x so the drawing matches what you see
X0, X1, Y0, Y1 = C.X_IN0, C.X_IN1, -C.IN_HY, C.IN_HY
cx.add_patch(FancyBboxPatch((F(X1), Y0), X1 - X0, Y1 - Y0, boxstyle="round,pad=0,rounding_size=%g" % (C.BOX_RC - C.WALL),
                            fc="#fafafa", ec=INK, lw=2.0))
# cell footprint (dashed) and cable bay
cx.add_patch(Rectangle((F(D.CT), -D.CW / 2), D.CT, D.CW, fc="#d7efe9", ec="#2e9e8a", lw=1.3, ls="--"))
cx.text(F(D.CT / 2), 0, "load cell\nabove\n(22 × 40)", ha="center", va="center", fontsize=8.5, color="#1f6f61")
cx.add_patch(Rectangle((F(D.CT), D.CW / 2), D.CT, Y1 - D.CW / 2, fc="none", ec="#e07a1f", lw=1.0, ls=":"))
cx.text(F(D.CT / 2), (D.CW / 2 + Y1) / 2, "cable bay\n18.5 mm", ha="center", va="center", fontsize=8, color="#b35a0f")
cx.add_patch(Rectangle((F(X1) + 1, C.COIL_Y0), X1 - X0 - 2, Y1 - C.COIL_Y0 - 1, fc="#f6c79a", ec="none", alpha=0.25, zorder=0))
cx.text(F(X1) + 2, 12, "spare cable\ncoils on the\nfloor here", fontsize=7.8, color="#b35a0f", ha="left", va="center")
# Nano
nx_l, nx_r = C.NANO_XL, C.NANO_XL + C.NANO_L
ny_l, ny_r = C.NANO_YC - C.NANO_W / 2, C.NANO_YC + C.NANO_W / 2
cx.add_patch(Rectangle((F(nx_r), ny_l), C.NANO_L, C.NANO_W, fc=PCB_BLUE, ec=INK, lw=1.3, alpha=0.95, zorder=2))
cx.add_patch(Rectangle((F(nx_l + 4), C.NANO_YC - 3.9), 6, 7.8, fc="#c9ccd1", ec=INK, lw=1))
p0 = C.NANO_XL + (C.NANO_L - 14 * 2.54) / 2
far_y, wall_y = C.NANO_YC + D.NANO_ROW / 2, C.NANO_YC - D.NANO_ROW / 2
for i in range(15):
    for yy, lst in ((far_y, FAR), (wall_y, WALL)):
        n = lst[i]
        used = n in USED or (n == "GND" and lst is FAR)
        cx.add_patch(Rectangle((F(p0 + i * 2.54) - 0.6, yy - 0.6), 1.2, 1.2, fc=PAD if used else "#9aa3ad", ec="none", zorder=3))
xf = F(p0 + 10 * 2.54)
cx.annotate("GND · D2 · D3", xy=(xf, far_y + 0.8), xytext=(F(X1) + 2, far_y + 6), fontsize=8.5, color=INK, fontweight="bold",
            ha="left", arrowprops=dict(arrowstyle="->", color=INK, lw=0.9), zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
x5 = F(p0 + 11 * 2.54)
cx.text(x5, wall_y + 1.4, "5V", fontsize=8, color=PAD, fontweight="bold", ha="center", va="bottom", zorder=4)
cx.text(F((nx_l + nx_r) / 2) + 3, C.NANO_YC, "Nano", ha="center", va="center", fontsize=10, color="white", fontweight="bold")
# HX711 against the -y wall
cx.add_patch(Rectangle((F(C.HX_X0 + C.HX_L), Y0), C.HX_L, C.HX_T, fc=HX_GREEN, ec=INK, lw=1.3))
cx.text(F(C.HX_X0 + C.HX_L / 2), Y0 - 1.5, "HX711 (on edge, on its shelf)", ha="center", va="top", fontsize=8, color=INK, zorder=4)
cx.annotate("jumper pads at THIS end\n(toward the finger side)", xy=(F(C.HX_X0 + C.HX_L) + 1.0, Y0 + C.HX_T), xytext=(F(X1) + 2, Y0 - 13.5),
            fontsize=8, color=INK, ha="left", va="top", arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
# USB window
cx.add_patch(Rectangle((F(X0) - 0.2, C.NANO_YC - C.WIN_W / 2), 3.2, C.WIN_W, fc="white", ec="#c0392b", lw=1.6))
cx.text(F(X0) + 4.5, C.NANO_YC, "USB\nwindow", fontsize=8, color="#c0392b", va="center", ha="left")
# wall labels
cx.text(F(X0) + 2.5, Y1 - 6, "PALM side", fontsize=9.5, color=GREY, ha="left", rotation=90, va="top")
cx.text(F(X1) - 2.5, Y1 - 6, "FINGER side", fontsize=9.5, color=GREY, ha="right", rotation=90, va="top")
cx.text(F((X0 + X1) / 2), Y1 + 2, "cable end wall", fontsize=9.5, color=GREY, ha="center", va="bottom")
cx.text(F((X0 + X1) / 2), Y0 - 6.5, "HX711 end wall", fontsize=9.5, color=GREY, ha="center", va="top")
room = C.HX_Z0 - (C.PCB_TOP + D.NANO_PIN)
cx.text(F(X1) - 1, Y0 - 24,
        f"Nano rides on the cover's rail, components facing into the box.\n"
        f"HX711 pads (far end from the USB) sit right above the Nano's\nD3 / D2 / GND / 5V pins: the jumpers run only about 4–6 cm.\n"
        f"Above the pin tips there is {room:.0f} mm before the HX711; a straight\nfemale plug needs about 8 mm, so bend the wires over gently.",
        fontsize=8.3, color=GREY, va="top", ha="left")
cx.set_xlim(F(X1) - 3, F(X0) + 12)
cx.set_ylim(Y0 - 52, Y1 + 8)
# 10 mm scale bar
sb = F(X1) + 2
cx.plot([sb, sb + 10], [Y1 + 5.5, Y1 + 5.5], color=INK, lw=2)
cx.text(sb + 5, Y1 + 6.3, "10 mm", fontsize=7.5, ha="center", va="bottom", color=INK)

out = os.path.join(IMG, "wiring_jumpers_v3.png")
fig.savefig(out, facecolor="white")
print("wrote", out)
