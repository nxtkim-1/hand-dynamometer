"""draw_dimensions.py — dimensioned side view, mount detail, calibration rig."""
import os, importlib.util
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms as mt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("d", os.path.join(HERE, "dynamometer_cad.py"))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
IMG = os.path.join(HERE, "..", "images"); os.makedirs(IMG, exist_ok=True)
PALM_C, FING_C, TEAL, AMBER = "#cfd2d8", "#a9adb6", "#2f9e8a", "#e0a030"

def palm_poly():
    return [(d.PALM_X0,d.CELL_Z0),(d.PALM_X1,d.CELL_Z0),(d.PALM_X1,d.HEAD_Z0),
            (d.HEAD_X1,d.HEAD_Z0),(d.HEAD_X1,d.HEAD_Z1),(d.PALM_X0,d.HEAD_Z1)]
def finger_poly():
    return [(d.FING_BAR_X0,d.FINGER_Z0),(d.FING_X1,d.FINGER_Z0),(d.FING_X1,d.FING_Z1),
            (d.FING_BOSS_X0,d.FING_Z1),(d.FING_BOSS_X0,d.FING_BOSS_Z0),
            (d.FING_BAR_X0,d.FING_BOSS_Z0)]

def body(ax, tr=None):
    kw = dict(transform=tr) if tr else {}
    ax.add_patch(Polygon(palm_poly(), closed=True, fc=PALM_C, ec="k", lw=1.0, **kw))
    ax.add_patch(Rectangle((d.PALM_X1,d.BOSS_Z0), d.PALM_BOSS, d.BOSS_Z1-d.BOSS_Z0,
                           fc=PALM_C, ec="k", lw=1.0, **kw))
    ax.add_patch(Rectangle((d.PALM_X1,d.BOSS_Z0), d.PALM_BOSS+d.LEDGE_X, d.LEDGE_T,
                           fc=AMBER, ec="k", lw=1.0, **kw))
    ax.add_patch(Rectangle((d.CELL_X0,d.CELL_Z0), d.CELL_T, d.CELL_L,
                           fc=TEAL, ec="k", lw=1.0, **kw))
    ax.add_patch(Polygon(finger_poly(), closed=True, fc=FING_C, ec="k", lw=1.0, **kw))
    ax.add_patch(Rectangle((d.CELL_X1-d.LEDGE_X,d.CELL_Z1), d.LEDGE_X+d.GAP, d.LEDGE_T,
                           fc=AMBER, ec="k", lw=1.0, **kw))
    for lo,hi in (d.SLOT_NEAR,d.SLOT_FAR):
        ax.add_patch(FancyBboxPatch((d.PALM_X0,d.CELL_Z0+lo), d.PALM_T+d.PALM_BOSS, hi-lo,
            boxstyle="round,pad=0,rounding_size=3", fc="white", ec="k", lw=0.7, **kw))
        ax.add_patch(FancyBboxPatch((d.CELL_X1,d.CELL_Z1-hi), d.FINGER_T+d.GAP, hi-lo,
            boxstyle="round,pad=0,rounding_size=3", fc="white", ec="k", lw=0.7, **kw))
    ax.add_patch(Rectangle((d.HEAD_X1+0.5,d.STOP_Z-3), d.FING_X1-d.HEAD_X1+6, 6,
                           fc=AMBER, ec="k", lw=1.0, **kw))
    ax.add_patch(Circle(((d.FING_BAR_X0+d.FING_X1)/2, d.HOOK_Z), d.HOOK_D/2,
                        fc="white", ec="k", lw=0.8, **kw))

# ---------------- side view ----------------
fig, ax = plt.subplots(figsize=(8.5,10))
body(ax)
def dh(x0,x1,y,t,off=5):
    ax.annotate("",(x0,y),(x1,y),arrowprops=dict(arrowstyle="<->",lw=0.9))
    ax.text((x0+x1)/2,y+off,t,ha="center",va="bottom",fontsize=9)
def dv(x,z0,z1,t,off=4):
    ax.annotate("",(x,z0),(x,z1),arrowprops=dict(arrowstyle="<->",lw=0.9))
    ax.text(x+off,(z0+z1)/2,t,ha="left",va="center",fontsize=9)
dh(d.PALM_X0,d.FING_X1,d.HEAD_Z1+14,f"grip span {d.GRIP_SPAN:.0f}")
for x in (d.PALM_X0, d.FING_X1):
    ax.plot([x,x],[d.HEAD_Z1,d.HEAD_Z1+14],lw=0.5,ls=":",color="k")
dv(d.FING_X1+14,d.FINGER_Z0,d.FING_BOSS_Z0,f"grip zone {d.FING_BOSS_Z0-d.FINGER_Z0:.0f}")
dv(d.PALM_X0-16,d.FINGER_Z0,d.HEAD_Z1,f"{d.HEAD_Z1-d.FINGER_Z0:.0f} overall")
ax.text(d.PALM_X0-3,95,"PALM part\nbolts to the cell's\nlower end",ha="right",va="center",fontsize=9)
ax.text(d.FING_X1+3,150,"FINGER part\nbolts to the cell's\nupper end",ha="left",va="center",fontsize=9)
ax.text(d.CELL_X0+d.CELL_T/2,85,"CZL601\n100 kg",ha="center",va="center",fontsize=8,color="white")
ax.text(d.FING_X1+8,d.STOP_Z,"M6 overload stop",fontsize=8,va="center")
ax.text(d.FING_X1+8,d.HOOK_Z,"calibration hook",fontsize=8,va="center")
ax.text(d.HEAD_X1+2,d.HEAD_Z1-5,"head block",fontsize=8,va="center",ha="left")
ax.text(d.PALM_X0-3,d.CELL_Z0+38,"M6 slots",fontsize=8,ha="right",va="center")
ax.text(d.FING_X1+3,d.CELL_Z1-40,"M6 slots",fontsize=8,ha="left",va="center")
ax.set_xlim(d.PALM_X0-56,d.FING_X1+66); ax.set_ylim(-18,d.HEAD_Z1+34)
ax.set_aspect("equal"); ax.grid(True,lw=0.3,alpha=0.35)
ax.set_xlabel("x (mm) — palm face x = -14, fingers pull in −x")
ax.set_ylabel("z (mm)")
ax.set_title("Hand dynamometer — side view, mm\nTwo printed parts on opposite faces of the cell. They never touch.")
fig.tight_layout(); fig.savefig(os.path.join(IMG,"drawing_side_dimensions.png"),dpi=150); plt.close(fig)

# ---------------- mount detail ----------------
fig, ax = plt.subplots(figsize=(8,7))
body(ax)
for lo,hi in (d.SLOT_NEAR,d.SLOT_FAR):
    ax.annotate("",(d.PALM_X0-6,d.CELL_Z0+lo),(d.PALM_X0-6,d.CELL_Z0+hi),
                arrowprops=dict(arrowstyle="<->",lw=0.9,color="#b03030"))
    ax.text(d.PALM_X0-8,d.CELL_Z0+(lo+hi)/2,f"{lo:.0f}–{hi:.0f}",ha="right",va="center",
            fontsize=8,color="#b03030")
ax.annotate("",(d.CELL_X0+4,d.CELL_Z0-9),(d.CELL_X0+4,d.CELL_Z0),
            arrowprops=dict(arrowstyle="->",lw=1.1,color="#b03030"))
ax.text(d.CELL_X0+6,d.CELL_Z0-11,"cell end face sits on the ledge —\nthe ledge sets position, not the bolts",
        fontsize=8,color="#b03030",va="top")
ax.text(d.FING_X1+6,70,f"{d.GAP:.0f} mm clear\nof the cell",fontsize=8,va="center")
ax.text(d.PALM_X1-2,110,f"{d.PALM_BOSS:.0f} mm clear\nof the cell",fontsize=8,va="center",ha="right")
ax.set_xlim(d.PALM_X0-44,d.FING_X1+52); ax.set_ylim(-4,d.CELL_Z1+16)
ax.set_aspect("equal"); ax.grid(True,lw=0.3,alpha=0.35)
ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
ax.set_title("Mount detail — ledges locate, slots clamp\nAny hole spacing in the red ranges assembles.",fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(IMG,"drawing_mount_detail.png"),dpi=150); plt.close(fig)

# ---------------- calibration rig ----------------
fig, ax = plt.subplots(figsize=(8.5,7))
tr = mt.Affine2D().rotate_deg(90) + ax.transData
body(ax, tr)
hx, hy = -d.HOOK_Z, (d.FING_BAR_X0+d.FING_X1)/2
ax.plot([hx,hx],[hy,hy-95], color="#333", lw=1.8)
ax.add_patch(Circle((hx,hy-112), 17, fc="#d8d8dc", ec="k", lw=1.0))
ax.text(hx+24,hy-112,"known mass\n(weigh it first)",fontsize=9,va="center")
ax.annotate("",(hx-30,hy-30),(hx-30,hy-80),arrowprops=dict(arrowstyle="->",lw=1.6,color="#b03030"))
ax.text(hx-36,hy-55,"gravity",fontsize=9,color="#b03030",va="center",ha="right")
ax.add_patch(Rectangle((-d.HEAD_Z1-6,-30),34,26,fc="#8a8d95",ec="k",lw=1.0))
ax.text(-d.HEAD_Z1+11,-34,"vise clamps the head block",ha="center",va="top",fontsize=9)
ax.text(-95,42,"finger bar",fontsize=9,ha="center")
ax.text(-95,-6,"palm plate",fontsize=9,ha="center")
ax.text(-175,-70,"Rotated 90°, gravity now pulls the finger bar toward the palm —\n"
                 "the same direction a squeeze does, through the same bolts.\n"
                 "The hook sits below the palm plate, so the cord hangs clear.",
        fontsize=9,color="#333",va="top")
ax.set_xlim(-200,70); ax.set_ylim(-100,80)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Calibration rig",fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(IMG,"drawing_calibration_rig.png"),dpi=150); plt.close(fig)
print("wrote three drawings")
