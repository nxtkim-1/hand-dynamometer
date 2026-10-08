"""
render_previews.py — makes preview PNGs of the assembly from the exported STLs.
Run after dynamometer_cad.py.   pip install trimesh matplotlib numpy
"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
IMG = os.path.join(HERE, "..", "images")
os.makedirs(IMG, exist_ok=True)

PARTS = {
    "palm": ("#cfd2d8", 1.0),
    "finger": ("#a9adb6", 1.0),
    "tray": ("#8f939c", 1.0),
    "load_cell_placeholder": ("#2f9e8a", 1.0),
}


def load(name, offset=(0, 0, 0)):
    m = trimesh.load(os.path.join(OUT, f"{name}.stl"))
    m.apply_translation(offset)
    return m


def shade(mesh, base_hex, light=np.array([0.4, -0.7, 0.6])):
    base = np.array(matplotlib.colors.to_rgb(base_hex))
    n = mesh.face_normals
    lam = np.clip(n @ (light / np.linalg.norm(light)), 0, 1)
    k = 0.45 + 0.55 * lam
    return np.clip(base[None, :] * k[:, None], 0, 1)


def draw(ax, meshes, elev, azim, title):
    allv = []
    for m, col in meshes:
        tri = m.vertices[m.faces]
        pc = Poly3DCollection(tri, facecolors=shade(m, col), edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
        allv.append(m.vertices)
    v = np.vstack(allv)
    c = (v.max(0) + v.min(0)) / 2
    r = (v.max(0) - v.min(0)).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=11)


def fig_single(meshes, elev, azim, title, fname, size=(7, 7)):
    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(111, projection="3d")
    draw(ax, meshes, elev, azim, title)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, fname), dpi=150)
    plt.close(fig)


assembled = [(load(n), c) for n, (c, _) in PARTS.items()]
fig_single(assembled, 22, -55, "Assembled — isometric", "assembly_iso.png")
fig_single(assembled, 0, -90, "Assembled — side view (palm on the left)", "assembly_side.png")
fig_single(assembled, 12, -30, "Assembled — three-quarter", "assembly_three_quarter.png")
fig_single(assembled, 90, -90, "Assembled — top view", "assembly_top.png")

exploded = [
    (load("palm", (-45, 0, 0)), PARTS["palm"][0]),
    (load("load_cell_placeholder"), PARTS["load_cell_placeholder"][0]),
    (load("finger", (45, 0, 0)), PARTS["finger"][0]),
    (load("tray", (-85, 0, 0)), PARTS["tray"][0]),
]
fig_single(exploded, 22, -55, "Exploded — parts pulled apart along their bolt axes", "assembly_exploded.png")

fig, axes = plt.subplots(1, 4, figsize=(16, 5), subplot_kw={"projection": "3d"})
for ax, name in zip(axes, ["palm", "finger", "tray", "fit_coupon"]):
    m = load(name)
    draw(ax, [(m, "#c9cbd2")], 25, -50, name)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "parts_individual.png"), dpi=150)
plt.close(fig)

for name in PARTS:
    m = load(name)
    print(f"{name:24s} watertight={m.is_watertight}  faces={len(m.faces)}")
print("wrote images to", os.path.abspath(IMG))
