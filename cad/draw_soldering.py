"""draw_soldering.py — what gets soldered to what: load cell -> HX711 -> Arduino Nano.
Writes images/soldering_guide.png.  Run:  python draw_soldering.py   (needs matplotlib)

Pin facts used:
  HX711 (24 x 16 board): left pads top-to-bottom  E+ E- A- A+ B- B+ ;  right pads top-to-bottom  GND DT SCK VCC
  Nano, USB at the BOTTOM, components up. Left column top-to-bottom:  TX1 RX0 RST GND D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12
                                          Right column top-to-bottom: VIN GND RST 5V A7 A6 A5 A4 A3 A2 A1 A0 REF 3V3 D13
  (always confirm against the labels printed on YOUR board before soldering)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

IMG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images"))
INK, GREY = "#1b1f24", "#7a7f87"
fig = plt.figure(figsize=(17, 11.5), dpi=140); fig.patch.set_facecolor("white")
fig.suptitle("Soldering guide — load cell → HX711 → Arduino Nano", x=0.04, y=0.975, ha="left",
             fontsize=17, fontweight="bold", color=INK)
fig.text(0.04, 0.932, "Match every label to the text printed on YOUR boards before you solder. Wire colours on the link wires "
         "are only a suggestion: use what you have and write the mapping in the build log.", fontsize=10, color=GREY)

ax = fig.add_axes([0.03, 0.30, 0.94, 0.64]); ax.set_xlim(-48, 112); ax.set_ylim(-38, 34); ax.set_aspect("equal"); ax.axis("off")

# ---------- HX711 (x 14..38, y 0..16) ----------
hx0, hy0 = 14, 0
ax.add_patch(Rectangle((hx0, hy0), 24, 16, fc="#cfe8d5", ec=INK, lw=1.8, zorder=2))
ax.text(hx0 + 12, hy0 + 17.8, "HX711", ha="center", fontsize=12, fontweight="bold", color=INK)
J1 = ["E+", "E−", "A−", "A+", "B−", "B+"]
JP2 = ["GND", "DT", "SCK", "VCC"]
j1y = {n: hy0 + 14 - i * 2.4 for i, n in enumerate(J1)}
jp2y = {n: hy0 + 12.5 - i * 2.8 for i, n in enumerate(JP2)}
for n, y in j1y.items():
    ax.add_patch(Circle((hx0 + 2.2, y), 0.8, fc="#e8c76a", ec=INK, zorder=3))
    ax.text(hx0 + 3.6, y, n, fontsize=8.5, va="center", color=INK, zorder=3, fontweight="bold" if n in ("E+", "E−", "A−", "A+") else "normal")
for n, y in jp2y.items():
    ax.add_patch(Circle((hx0 + 21.8, y), 0.8, fc="#e8c76a", ec=INK, zorder=3))
    ax.text(hx0 + 20.4, y, n, fontsize=8.5, va="center", ha="right", color=INK, zorder=3, fontweight="bold")
ax.text(hx0 - 0.5, hy0 - 2.4, "← from the load cell", fontsize=8.5, color=GREY, ha="left")
ax.text(hx0 + 24.5, hy0 - 2.4, "to the Nano →", fontsize=8.5, color=GREY, ha="right")
ax.text(hx0 + 3.6, hy0 + 2.0 - 0.0, "(B− B+ stay empty)", fontsize=7, color=GREY, va="center", zorder=3) if False else None

# ---------- load cell cable (left) ----------
ax.add_patch(Rectangle((-46, 6), 17, 9, fc="#dfe3e8", ec=INK, lw=1.6))
ax.text(-37.5, 10.5, "load cell", ha="center", va="center", fontsize=10, fontweight="bold")
ax.plot([-29, -22], [10.5, 10.5], color="#2a2d33", lw=9, solid_capstyle="butt")           # cable jacket
ax.text(-25.5, 16.5, "cable ∅ 5.13", ha="center", fontsize=8, color=GREY)
wires = [("red", "#d62828", "E+"), ("black", "#111111", "E−"), ("white", "#ffffff", "A−"), ("green", "#2a9d4a", "A+")]
for k, (name, col, pad) in enumerate(wires):
    y_start = 12.6 - k * 1.7
    xs = [-22, -17, 4 + 0, hx0 + 2.2]
    ys = [y_start, y_start, j1y[pad], j1y[pad]]
    ax.plot(xs, ys, color=INK, lw=5.2, solid_capstyle="round", zorder=1)
    ax.plot(xs, ys, color=col, lw=3.6, solid_capstyle="round", zorder=1.1)
    ax.text(-17, y_start + (0.0), f" {name}", fontsize=8.5, va="center", ha="left", color=INK, zorder=4,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
    ax.text(5.2, j1y[pad] + 0.0, f"{name} → {pad}", fontsize=8.5, va="center", ha="right", color=INK, fontweight="bold", zorder=4,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9)) if False else None
ax.plot([-22, -16], [3.0, 3.0], color="#d4b106", lw=3.0, ls=(0, (2, 1.5)), solid_capstyle="round")
ax.text(-15.2, 1.2, "yellow = shield:\ndo NOT solder it,\ntape over the end", fontsize=8, va="center", color="#8a6d00")

# ---------- Nano (USB at bottom). x 60..78.11, y -8..36 -> drawn y -34..10 ----------
nx0, ny0, NW, NL = 66, -34.0, 18.11, 44.0
ax.add_patch(Rectangle((nx0, ny0), NW, NL, fc="#c9d3e6", ec=INK, lw=1.8, zorder=2))
ax.add_patch(Rectangle((nx0 + NW / 2 - 4, ny0 - 2.0), 8, 7, fc="#aeb4be", ec=INK, lw=1.2, zorder=2))
ax.text(nx0 + NW / 2, ny0 - 4.0, "USB", ha="center", fontsize=8.5, color=GREY)
left = ["TX1", "RX0", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"]
right = ["VIN", "GND", "RST", "5V", "A7", "A6", "A5", "A4", "A3", "A2", "A1", "A0", "REF", "3V3", "D13"]
used = {"GND", "D2", "D3", "5V"}
ly, ry = {}, {}
for i, n in enumerate(left):
    y = ny0 + NL - 2.0 - i * 2.54
    ly[(n, i)] = y
    ax.add_patch(Circle((nx0 + 1.4, y), 0.75, fc="#e8c76a" if n in used else "white", ec=INK, zorder=3, lw=0.8))
    ax.text(nx0 + 2.9, y, n, fontsize=7.5 if n in used else 6, va="center", color=INK if n in used else GREY, zorder=3,
            fontweight="bold" if n in used else "normal")
for i, n in enumerate(right):
    y = ny0 + NL - 2.0 - i * 2.54
    ry[(n, i)] = y
    ax.add_patch(Circle((nx0 + NW - 1.4, y), 0.75, fc="#e8c76a" if n == "5V" else "white", ec=INK, zorder=3, lw=0.8))
    ax.text(nx0 + NW - 2.9, y, n, fontsize=7.5 if n == "5V" else 6, va="center", ha="right",
            color=INK if n == "5V" else GREY, zorder=3, fontweight="bold" if n == "5V" else "normal")
ax.text(nx0 + NW / 2, ny0 - 8.0, "Arduino Nano (USB at the bottom, chip side up)", ha="center", fontsize=10, fontweight="bold")
ax.text(nx0 + NW / 2, ny0 + NL - 0.2, "", fontsize=7)

ypin = {"GND": ly[("GND", 3)], "D2": ly[("D2", 4)], "D3": ly[("D3", 5)], "5V": ry[("5V", 3)]}
links = [("GND", "GND", "#111111", "black"), ("DT", "D3", "#1f6feb", "blue"),
         ("SCK", "D2", "#e07b00", "orange"), ("VCC", "5V", "#d62828", "red")]
route_x = {"GND": 50, "DT": 54.5, "SCK": 59.0, "VCC": 46}
for k, (pad, pin, col, cname) in enumerate(links):
    y0 = hy0 + jp2y[pad] - hy0
    x0 = hx0 + 21.8
    if pin == "5V":                              # goes over the top of the board to the right-hand column
        xs = [x0, 46, 46, nx0 + NW + 4.0, nx0 + NW + 4.0, nx0 + NW - 1.4]
        ys = [y0, y0, ny0 + NL + 6.5, ny0 + NL + 6.5, ypin[pin], ypin[pin]]
    else:
        rx = route_x[pad]
        xs = [x0, rx, rx, nx0 + 1.4]
        ys = [y0, y0, ypin[pin], ypin[pin]]
    ax.plot(xs, ys, color=INK, lw=4.8, solid_capstyle="round", zorder=1)
    ax.plot(xs, ys, color=col, lw=3.2, solid_capstyle="round", zorder=1.1)
ax.text(46, ny0 + NL + 8.0, "5V wire runs over the top end of the board", fontsize=8, color="#d62828")

# legend table (right side)
rows = [("HX711 GND", "Nano GND", "black"), ("HX711 DT", "Nano D3", "blue"),
        ("HX711 SCK", "Nano D2", "orange"), ("HX711 VCC", "Nano 5V", "red")]
ax.text(92, 30, "Link wires (suggested colours)", fontsize=10, fontweight="bold", va="center")
for i, (a, b, c) in enumerate(rows):
    ax.text(92, 26.5 - i * 3.1, f"{a}  →  {b}   ({c})", fontsize=9.5, va="center")
ax.text(92, 12.5, "Load cell → HX711", fontsize=10, fontweight="bold", va="center")
for i, (a, b) in enumerate((("red", "E+"), ("black", "E−"), ("white", "A−"), ("green", "A+"))):
    ax.text(92, 9.0 - i * 3.1, f"{a}  →  {b}", fontsize=9.5, va="center")
ax.text(92, -4.0, "Pad order on the HX711 is\nE+  E−  A−  A+ — not the usual\ncolour order. Read the labels.", fontsize=8.5, color="#b45309", va="top")

# ---------- how to solder + checks ----------
fig.text(0.04, 0.265, "How to make each joint (about 2 minutes each)", fontsize=12, fontweight="bold", color=INK)
steps = [
    "1.  Iron at about 330–350 °C. Strip 3–4 mm from the wire, twist the strands, melt a little solder onto them (tin them).",
    "2.  Put a little solder on the pad too (1–2 s). Pads that are already tinned join in seconds.",
    "3.  Lay the wire on the pad. Touch the iron to wire and pad together for about 2 s, feed a touch of solder to the joint, take the solder away, then the iron.",
    "4.  Hold still for 2 s while it sets. A good joint is shiny, smooth and cone-shaped. Dull, grainy or balled-up = cold joint: reheat it.",
    "5.  Tug each wire gently. Then add a zip tie or dab of hot glue on the cable so a pull goes into the tie and never into the pad.",
]
for i, t in enumerate(steps):
    fig.text(0.04, 0.238 - i * 0.026, t, fontsize=10, color=INK)
fig.text(0.04, 0.098, "Checks before you plug in USB", fontsize=12, fontweight="bold", color=INK)
checks = [
    "•  Meter on continuity: each joint beeps to its wire; neighbouring pads do NOT beep to each other.",
    "•  Meter on ohms at the HX711 pads (power OFF): E+ to E− is about 405 Ω, and A+ to A− is about 350 Ω. If not, a wire is on the wrong pad.",
    "•  5V and GND are the two that can hurt a board if swapped. Look at both ends of the red and black link wires once more.",
]
for i, t in enumerate(checks):
    fig.text(0.04, 0.072 - i * 0.026, t, fontsize=10, color=INK)
fig.savefig(os.path.join(IMG, "soldering_guide.png"), dpi=140, facecolor="white")
print("wrote soldering_guide.png")
