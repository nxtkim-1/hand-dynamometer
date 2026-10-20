"""render_design_a.py — preview images for Design A."""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output_design_a")
IMG = os.path.join(HERE, "..", "images", "design_a")
os.makedirs(IMG, exist_ok=True)

COL = {"housing": "#d4d6db", "lid": "#d4d6db", "handle": "#3a3d44", "cell": "#2f9e8a"}
LIGHT = np.array([0.35, -0.55, 0.75]); LIGHT /= np.linalg.norm(LIGHT)


def load(n, off=(0, 0, 0)):
    m = trimesh.load(os.path.join(OUT, f"{n}.stl"))
    m.apply_translation(off)
    return m


def colours(m, hexc, alpha):
    base = np.array(matplotlib.colors.to_rgb(hexc))
    lam = np.clip(m.face_normals @ LIGHT, -1, 1)
    k = 0.52 + 0.48 * np.clip(lam, 0, 1) - 0.08 * np.clip(-lam, 0, 1)
    rgb = np.clip(base[None, :] * k[:, None], 0, 1)
    return np.hstack([rgb, np.full((len(rgb), 1), alpha)])


def render(items, elev, azim, fname, title=None, size=(7, 7)):
    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(111, projection="3d")
    allv = []
    for m, c, a in items:
        pc = Poly3DCollection(m.vertices[m.faces], facecolors=colours(m, c, a),
                              edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
        allv.append(m.vertices)
    v = np.vstack(allv)
    ctr = (v.max(0) + v.min(0)) / 2
    r = (v.max(0) - v.min(0)).max() / 2 * 0.9
    ax.set_xlim(ctr[0] - r, ctr[0] + r); ax.set_ylim(ctr[1] - r, ctr[1] + r); ax.set_zlim(ctr[2] - r, ctr[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, fname), dpi=160, facecolor="white")
    plt.close(fig)


H, L, D, C = load("housing"), load("lid"), load("handle"), load("cell")
solid = [(H, COL["housing"], 1), (L, COL["lid"], 1), (D, COL["handle"], 1)]

render(solid, 18, -50, "a_hero.png", "Design A — assembled")
render(solid, 14, 130, "a_back.png", "Design A — palm side")
render(solid, 0, 0, "a_side.png", "Design A — side (palm left, fingers right)")
render([(H, COL["housing"], 0.22), (L, COL["lid"], 0.12), (D, COL["handle"], 1), (C, COL["cell"], 1)],
       18, -50, "a_see_through.png", "See-through: the load cell inside the head")
render([(H, COL["housing"], 1),
        (L.copy().apply_translation((0, 0, 55)), COL["lid"], 1),
        (C.copy().apply_translation((0, 0, 28)), COL["cell"], 1),
        (D.copy().apply_translation((55, 0, 0)), COL["handle"], 1)],
       20, -55, "a_exploded.png", "Exploded — housing, load cell, lid, handle", size=(8, 8))
print("rendered to", os.path.abspath(IMG))
