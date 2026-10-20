"""draw_final.py — dimensioned side-section drawing. Run after dynamometer_cad.py."""
import os
import importlib.util
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("d", os.path.join(HERE, "dynamometer_cad.py"))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
IMG = os.path.join(HERE, "..", "images")
GREY, BLACK, TEAL = "#d9dbe0", "#34363c", "#2f9e8a"

r_pts = np.array([30.0] + [r for r, z in d.PROFILE] + [0.0])
z_pts = np.array([d.Z_BOT] + [z for r, z in d.PROFILE] + [d.Z_TOP])
zz = np.linspace(d.Z_BOT, d.Z_TOP, 400)
rr = np.interp(zz, z_pts, r_pts)


def band(z0, z1, side):
    m = (zz >= z0) & (zz <= z1)
    z, r = zz[m], rr[m]
    if side == "palm":
        return list(zip(d.AX - r, z)) + [(d.AX - d.SEAM, z1), (d.AX - d.SEAM, z0)]
    return list(zip(d.AX + r, z)) + [(d.AX + d.SEAM, z1), (d.AX + d.SEAM, z0)]


def full(z0, z1):
    m = (zz >= z0) & (zz <= z1)
    z, r = zz[m], rr[m]
    return list(zip(d.AX - r, z)) + list(zip((d.AX + r)[::-1], z[::-1]))


fig, ax = plt.subplots(figsize=(8.5, 11))
ax.add_patch(Polygon(full(d.Z_BOT, d.Z_COVER), fc=GREY, ec="k", lw=0.9))
ax.add_patch(Polygon(full(d.Z_COVER, d.Z_POD_TOP), fc=GREY, ec="k", lw=0.9))
ax.add_patch(Polygon(band(d.Z_POD_TOP, d.Z_PALM_TOP, "palm"), fc=GREY, ec="k", lw=0.9))
ax.add_patch(Polygon(band(d.Z_FINGER_BOT, d.Z_DOME, "finger"), fc=BLACK, ec="k", lw=0.9))
ax.add_patch(Polygon(full(d.Z_DOME, d.Z_TOP), fc=BLACK, ec="k", lw=0.9))
# hollow bore and pod (drawn white)
ax.add_patch(Rectangle((-d.GAP, d.Z_POD_TOP), d.CT + 2 * d.GAP, d.Z_DOME - d.Z_POD_TOP, fc="white", ec="none"))  # pocket: 3 mm around the cell
ax.add_patch(Rectangle((d.AX - d.POD_BORE, d.Z_COVER), 2 * d.POD_BORE, d.Z_POD_TOP - d.Z_COVER, fc="white", ec="none"))
# internal features
ax.add_patch(Rectangle((-12, 0), 12, d.CLAMP, fc=GREY, ec="k", lw=0.8))                 # palm boss
ax.add_patch(Rectangle((-12, -3), 17, 3, fc="#e0a030", ec="k", lw=0.8))                 # ledge
ax.add_patch(Polygon([(-12, -3), (5, -3), (-12, -20)], fc=GREY, ec="k", lw=0.8))        # gusset
ax.add_patch(Rectangle((d.CT, d.CL - d.CLAMP), 11.6, d.CLAMP + 3, fc=BLACK, ec="k", lw=0.8))  # finger boss
ax.add_patch(Rectangle((d.CT - 5, d.CL), 13, 3, fc="#e0a030", ec="k", lw=0.8))         # top ledge
ax.add_patch(Rectangle((0, 0), d.CT, d.CL, fc=TEAL, ec="k", lw=0.9))                     # load cell
ax.add_patch(Circle((d.AX, d.HOOK_Z), 3.3, fc="white", ec="k", lw=0.8))
for z in d.GROOVES_Z:
    ax.add_patch(Circle((d.AX + 35.5, z), 10, fc="white", ec="none"))


def dim_v(x, z0, z1, text, side="right"):
    ax.annotate("", (x, z0), (x, z1), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(x + (3 if side == "right" else -3), (z0 + z1) / 2, text, ha="left" if side == "right" else "right",
            va="center", fontsize=9)


def dim_h(x0, x1, z, text):
    ax.annotate("", (x0, z), (x1, z), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((x0 + x1) / 2, z + 3, text, ha="center", va="bottom", fontsize=9)


dim_v(d.AX + 46, d.Z_BOT, d.Z_TOP, f"{d.Z_TOP - d.Z_BOT:.0f} overall")
dim_v(d.AX - 46, d.Z_FINGER_BOT, d.Z_PALM_TOP, f"grip {d.Z_PALM_TOP - d.Z_FINGER_BOT:.0f}", side="left")
dim_h(d.AX - 29, d.AX + 29, 58 + 60, "Ø58 at the fullest = grip span")
ax.plot([d.AX - 29, d.AX - 29], [58, 116], lw=0.5, ls=":", c="k"); ax.plot([d.AX + 29, d.AX + 29], [58, 116], lw=0.5, ls=":", c="k")
dim_h(d.AX - 30, d.AX + 30, d.Z_BOT - 10, "Ø60 base")

notes = [((d.AX - 14, 30), "boss: clamps the cell's\nlower end (2 × M6)"),
         ((d.AX - 18, -10), "ledge + 45° gusset:\nthe cell stands here"),
         ((d.AX + 20, 100), "boss: clamps the upper\nend (2 × M6)"),
         ((d.AX, -26), "electronics pod"),
         ((d.AX + 12, d.HOOK_Z + 2), "calibration hook"),
         ((d.AX + 34, 40), "finger\ngrooves"),
         ((d.AX, 65), "CZL601\n100 kg")]
for (x, z), t in notes:
    ax.text(x, z, t, fontsize=8, ha="center", va="center",
            color="white" if "CZL" in t else "k")
ax.text(d.AX, d.Z_PALM_TOP + 1.5, "3 mm seam", fontsize=7, ha="center", va="center")
ax.text(d.AX - 60, 145, "PALM HALF\n(grey)", fontsize=10, ha="center", fontweight="bold")
ax.text(d.AX + 62, 145, "FINGER HALF\n(black)", fontsize=10, ha="center", fontweight="bold")
ax.set_xlim(d.AX - 90, d.AX + 90); ax.set_ylim(d.Z_BOT - 25, d.Z_TOP + 15)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Hand dynamometer — section through the centre, mm\n"
             "Grey bolts to the bottom of the load cell, black to the top. They never touch.", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(IMG, "final_drawing.png"), dpi=150)
print("wrote final_drawing.png")
