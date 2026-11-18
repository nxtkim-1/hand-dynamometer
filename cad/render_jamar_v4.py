"""render_jamar_v4.py — VTK renders + annotated cutaway + flat-bed print plate check for jamar_v4.py."""
import os
import cadquery as cq
import vtk
from PIL import Image, ImageDraw, ImageFont
import jamar_v4 as J
import dynamometer_cad as D

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, "..", "images"))
TMP = os.path.join(D.OUT, "_render_jamar_v4")
os.makedirs(TMP, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

GREY = (0.84, 0.86, 0.89)
PALM = (0.68, 0.71, 0.76)
BLACK = (0.16, 0.18, 0.21)
POD = (0.26, 0.29, 0.34)
TEAL = (0.18, 0.62, 0.54)
ORANGE = (0.85, 0.42, 0.10)
BLUE = (0.20, 0.45, 0.85)
GREEN = (0.15, 0.62, 0.33)
BED_COL = (0.93, 0.94, 0.96)


def export(name, part, tol=0.03):
    p = os.path.join(TMP, f"{name}.stl")
    cq.exporters.export(part, p, tolerance=tol, angularTolerance=0.12)
    return p


def actor(path, col, op=1.0, edges=True):
    r = vtk.vtkSTLReader()
    r.SetFileName(path)
    n = vtk.vtkPolyDataNormals()
    n.SetInputConnection(r.GetOutputPort())
    n.SetFeatureAngle(35)
    n.SplittingOn()
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(m)
    pr = a.GetProperty()
    pr.SetColor(*col)
    pr.SetOpacity(op)
    pr.SetAmbient(0.26)
    pr.SetDiffuse(0.74)
    pr.SetSpecular(0.22)
    pr.SetSpecularPower(32)
    out = [a]
    if edges:
        fe = vtk.vtkFeatureEdges()
        fe.SetInputConnection(r.GetOutputPort())
        fe.BoundaryEdgesOff()
        fe.ManifoldEdgesOff()
        fe.NonManifoldEdgesOff()
        fe.SetFeatureAngle(40)
        em = vtk.vtkPolyDataMapper()
        em.SetInputConnection(fe.GetOutputPort())
        em.ScalarVisibilityOff()
        e = vtk.vtkActor()
        e.SetMapper(em)
        e.GetProperty().SetColor(0.08, 0.09, 0.11)
        e.GetProperty().SetOpacity(0.42 * op)
        out.append(e)
    return out


def render(groups, azim, elev, fname, focus, scale=None, zoom=1.0, size=1200):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for g in groups:
        for a in g:
            ren.AddActor(a)
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(40)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(size, size)
    win.AddRenderer(ren)
    win.SetAlphaBitPlanes(1)
    win.SetMultiSamples(0)
    cam = ren.GetActiveCamera()
    cam.SetViewUp(0, 0, 1)
    cam.SetFocalPoint(*focus)
    cam.SetPosition(focus[0], focus[1] - 1, focus[2])
    ren.ResetCamera()
    cam.Azimuth(azim)
    cam.Elevation(elev)
    cam.OrthogonalizeViewUp()
    if scale:
        cam.ParallelProjectionOn()
        cam.SetFocalPoint(*focus)
        d = cam.GetDirectionOfProjection()
        cam.SetPosition(focus[0] - d[0] * 800, focus[1] - d[1] * 800, focus[2] - d[2] * 800)
        cam.SetParallelScale(scale)
        ren.ResetCameraClippingRange()
    else:
        ren.ResetCamera()
        cam.Zoom(zoom)
    li = vtk.vtkLight()
    li.SetLightTypeToCameraLight()
    li.SetPosition(0.6, 0.8, 1)
    li.SetIntensity(0.9)
    ren.AddLight(li)
    win.Render()
    w = vtk.vtkWindowToImageFilter()
    w.SetInput(win)
    w.Update()
    out = os.path.join(IMG, fname)
    pw = vtk.vtkPNGWriter()
    pw.SetFileName(out)
    pw.SetInputConnection(w.GetOutputPort())
    pw.Write()
    return out


if __name__ == "__main__":
    fr, pb, fg, pc, gl = J.frame(), J.palm_bar(), J.finger(), J.pod_cover(), J.guard_left()
    cell = D.cell()
    pcb, nano_rest = J.nano_env()
    nano = pcb.union(nano_rest)
    hx = J.hx_env()
    cz, _ = J.coil_zone()
    ct = J.cable_tube()

    F = export("frame", fr)
    P = export("palm", pb)
    K = export("finger", fg)
    C = export("pod", pc)
    G = export("guard", gl)
    L = export("cell", cell)
    T = export("cable", ct)
    N = export("nano", nano)
    H = export("hx", hx)
    Z = export("coil", cz)

    focus = ((J.ARM_X0 + J.BX1_LO) / 2, 0, 50)

    # 1. Isometric hero render
    render(
        [actor(F, GREY), actor(P, PALM), actor(K, BLACK), actor(C, POD), actor(G, POD)],
        -38, 18, "jamar_v4_view.png", focus, zoom=1.08,
    )

    # 2. Open +y electronics & cable bay view (pod_cover removed)
    render(
        [actor(F, GREY), actor(P, PALM), actor(K, BLACK), actor(G, POD),
         actor(L, TEAL), actor(T, ORANGE), actor(Z, ORANGE, op=0.28, edges=False),
         actor(N, BLUE), actor(H, GREEN)],
        138, 18, "jamar_v4_open_bay.png", focus, zoom=1.05,
    )

    # 3. Annotated mid-plane cutaway (y = 0)
    half = D.box(-300, 300, 0, 300, -100, 300)
    Fs, Ps, Ks, Ls = (export(n + "_cut", p.intersect(half)) for n, p in (("frame", fr), ("palm", pb), ("finger", fg), ("cell", cell)))
    S = 136.0
    sec_focus = (focus[0] + 4, 0, 48)
    side = render(
        [actor(Fs, GREY), actor(Ps, PALM), actor(Ks, BLACK), actor(Ls, TEAL),
         actor(T, ORANGE), actor(Z, ORANGE, op=0.28, edges=False),
         actor(N, BLUE), actor(H, GREEN)],
        0, 0, "jamar_v4_section.png", sec_focus, scale=S,
    )
    im = Image.open(side).convert("RGB")
    W = im.width
    k = (W / 2) / S
    px = lambda x, z: (W / 2 + (x - sec_focus[0]) * k, W / 2 - (z - sec_focus[2]) * k)
    dr = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        f1 = f2 = ImageFont.load_default()

    def hdim(x0, x1, z, text):
        a, b = px(x0, z), px(x1, z)
        dr.line([a, b], fill=(31, 78, 156), width=3)
        for p in (a, b):
            dr.line([(p[0], p[1] - 9), (p[0], p[1] + 9)], fill=(31, 78, 156), width=3)
        dr.text(((a[0] + b[0]) / 2, a[1] - 16), text, fill=(31, 78, 156), font=f2, anchor="mm")

    g = J.GAPS[J.POS]
    xpb = J.FB_X0 - g
    hdim(xpb, J.FB_X0, 72, f"{g:.0f} mm gap")
    hdim(xpb - J.PB_T, J.FB_X1, 10, f"grip span {g + J.PB_T + J.FB_X1 - J.FB_X0:.0f} mm (pos 2 of 5)")
    dr.text(px(xpb - J.PB_T / 2, 162), "ergo palm bar", fill=(27, 31, 36), font=f1, anchor="mm")
    dr.text(px((J.FB_X0 + J.FB_X1) / 2, 162), "4-finger trigger", fill=(27, 31, 36), font=f1, anchor="mm")
    dr.text(px(16, 162), "tapered body", fill=(27, 31, 36), font=f1, anchor="mm")
    dr.text(px(16, -63), "Nano + HX711 + uncut coil + USB window", fill=(31, 78, 156), font=f2, anchor="mm")
    dr.text((24, 20), "v4 Jamar-style redesign: flat-print ergonomics + closed bay", fill=(27, 31, 36), font=f1)
    dr.text((24, 52), "grey = fixed frame + palm bar   black = finger trigger   teal = cell   orange = cable/coil   blue/green = Nano/HX711", fill=(105, 110, 118), font=f2)
    im.save(side)

    # 4. Support-free print plate layout (two 256 x 256 mm Bambu P1S/P2S plates side by side)
    plate1_base = D.box(0, 256, 0, 256, -2, 0)
    plate2_base = D.box(276, 276 + 256, 0, 256, -2, 0)
    fr_bed = J.to_flat_bed(fr).translate((26, 22, 0))
    # Inside frame C-window: x spans ~0..140, y spans ~85..191 -> center palm_bar cleanly inside window
    pb_bed = J.to_flat_bed(pb).translate((62, 107, 0))
    fg_bed = J.to_flat_bed(fg).translate((294, 30, 0))
    pc_bed = J.to_pod_bed(pc).translate((364, 22, 0))
    gl_bed = J.to_flat_bed(gl).translate((434, 22, 0))

    p_img = render(
        [
            actor(export("p1", plate1_base), BED_COL),
            actor(export("p2", plate2_base), BED_COL),
            actor(export("fr_bed", fr_bed), GREY),
            actor(export("pb_bed", pb_bed), PALM),
            actor(export("fg_bed", fg_bed), BLACK),
            actor(export("pc_bed", pc_bed), POD),
            actor(export("gl_bed", gl_bed), POD),
        ],
        -25, 42, "jamar_v4_print_plates.png", (266, 128, 14), zoom=1.18, size=1400,
    )
    print("Renders written:", p_img)
