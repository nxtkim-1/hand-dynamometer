"""render_compact.py — pictures of DRAFT v3 (compact box) and a same-scale comparison with dish v2.
Run after compact_base_draft.py (and dish_base_draft.py, for the comparison).  Needs cadquery + vtk + pillow."""
import os
import cadquery as cq
import vtk
from PIL import Image, ImageDraw, ImageFont

import compact_base_draft as C
import dynamometer_cad as D

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, "..", "images"))
TMP = os.path.join(D.OUT, "_render_compact")
os.makedirs(TMP, exist_ok=True)

GREY, BLACK, TEAL = (0.86, 0.87, 0.89), (0.17, 0.18, 0.21), (0.18, 0.62, 0.54)
ORANGE, BLUE, GREEN, COVER = (0.85, 0.42, 0.10), (0.20, 0.45, 0.80), (0.15, 0.62, 0.33), (0.70, 0.72, 0.75)


def export(name, part, tol=0.04):
    path = os.path.join(TMP, f"{name}.stl")
    cq.exporters.export(part, path, tolerance=tol, angularTolerance=0.15)
    return path


def actor(path, colour, opacity=1.0, edges=True):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(35); n.SplittingOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*colour); p.SetOpacity(opacity)
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.2); p.SetSpecularPower(30)
    acts = [a]
    if edges:
        fe = vtk.vtkFeatureEdges(); fe.SetInputConnection(r.GetOutputPort())
        fe.BoundaryEdgesOff(); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.SetFeatureAngle(40)
        em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort()); em.ScalarVisibilityOff()
        e = vtk.vtkActor(); e.SetMapper(em)
        e.GetProperty().SetColor(0.1, 0.1, 0.12); e.GetProperty().SetOpacity(0.45 * opacity)
        acts.append(e)
    return acts


def render(groups, azim, elev, fname, zoom=0.95, size=1200, scale=None, focus=None, roll=0.0):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for g in groups:
        for a in g:
            ren.AddActor(a)
    ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(40)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(size, size); win.AddRenderer(ren)
    win.SetAlphaBitPlanes(1); win.SetMultiSamples(0)
    cam = ren.GetActiveCamera(); cam.SetViewUp(0, 0, 1)
    f = focus or (C.AX, 0, 50)
    cam.SetFocalPoint(*f); cam.SetPosition(f[0], f[1] - 1, f[2])
    ren.ResetCamera(); cam.Azimuth(azim); cam.Elevation(elev); cam.OrthogonalizeViewUp()
    if roll:
        cam.Roll(roll)
    if scale:
        cam.ParallelProjectionOn(); cam.SetFocalPoint(*f)
        d = 600.0
        dop = cam.GetDirectionOfProjection()
        cam.SetPosition(f[0] - dop[0] * d, f[1] - dop[1] * d, f[2] - dop[2] * d)
        cam.SetParallelScale(scale)
        ren.ResetCameraClippingRange()
    else:
        ren.ResetCamera(); cam.Zoom(zoom)
    li = vtk.vtkLight(); li.SetLightTypeToCameraLight(); li.SetPosition(0.6, 0.8, 1); li.SetIntensity(0.9); ren.AddLight(li)
    win.Render()
    w = vtk.vtkWindowToImageFilter(); w.SetInput(win); w.Update()
    out = os.path.join(IMG, fname)
    pw = vtk.vtkPNGWriter(); pw.SetFileName(out); pw.SetInputConnection(w.GetOutputPort()); pw.Write()
    return out


if __name__ == "__main__":
    pm, fg, cv, cell = C.palm_compact(), C.finger_compact(), C.cover_compact(), D.cell()
    pcb, rest = C.nano_env()
    nano = pcb.union(rest)
    P, F, V, L = export("palm", pm), export("finger", fg), export("cover", cv), export("cell", cell)
    T, Z = export("cable", C.cable_tube()), export("coil", C.coil_zone())
    N, H = export("nano", nano), export("hx", C.hx_env())

    # 1. assembled, from the finger side and the cable (+y) end
    render([actor(P, GREY), actor(F, BLACK), actor(V, COVER)], 125, 14, "compact_v3_assembled.png", zoom=0.92)
    # 2. assembled, palm side (USB window, counterbores)
    render([actor(P, GREY), actor(F, BLACK), actor(V, COVER)], -55, 14, "compact_v3_palm_side.png", zoom=0.92)

    # 3. section on the plane through the cable (x = CXC), seen from +x
    half = D.box(-80, C.CXC, -80, 80, -80, 200)
    Ps, Fs, Vs, Ls = (export(f"{n}_cut", p.intersect(half)) for n, p in
                      (("palm", pm), ("finger", fg), ("cover", cv), ("cell", cell)))
    Zs = export("coil_cut", C.coil_zone().intersect(half))
    render([actor(Ps, GREY), actor(Fs, BLACK), actor(Vs, COVER), actor(Ls, TEAL),
            actor(T, ORANGE), actor(Zs, ORANGE, opacity=0.35, edges=False), actor(N, BLUE), actor(H, GREEN)],
           90, 0, "compact_v3_section.png", scale=112, focus=(C.CXC, 0, 48))
    # 3b. close-up of the cable bay
    render([actor(Ps, GREY), actor(Fs, BLACK), actor(Vs, COVER), actor(Ls, TEAL),
            actor(T, ORANGE), actor(Zs, ORANGE, opacity=0.35, edges=False), actor(N, BLUE), actor(H, GREEN)],
           90, 0, "compact_v3_cable_bay.png", scale=42, focus=(C.CXC, 12, -14))

    # 4. inside the base: cover removed, looking up from below
    render([actor(P, GREY), actor(T, ORANGE), actor(Z, ORANGE, opacity=0.35, edges=False),
            actor(N, BLUE), actor(H, GREEN), actor(L, TEAL)], 35, -62, "compact_v3_inside.png", zoom=1.6,
           focus=(C.AX, 0, -25))

    # 5. same-scale comparison with dish v2 (read from its STEP files, assembly coordinates)
    dd = os.path.join(D.OUT, "draft_dish")
    dish = {}
    for n, col in (("palm_dish", GREY), ("finger_dish", BLACK), ("plug", COVER)):
        stp = os.path.join(dd, f"{n}_v2_DRAFT.step")
        if os.path.exists(stp):
            dish[n] = (export(f"dish_{n}", cq.importers.importStep(stp)), col)
    shots = []
    shots.append(render([actor(P, GREY), actor(F, BLACK), actor(V, COVER)], 125, 14, "_cmp_compact.png",
                        scale=125, focus=(C.AX, 0, 50), size=900))
    if dish:
        shots.append(render([actor(p, c) for p, c in dish.values()], 125, 14, "_cmp_dish.png",
                            scale=125, focus=(C.AX, 0, 50), size=900))
    ims = [Image.open(s) for s in shots]
    W = sum(i.width for i in ims)
    canvas = Image.new("RGB", (W, ims[0].height + 90), "white")
    x = 0
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        small = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font = small = ImageFont.load_default()
    labels = [("A  compact box (v3, new)", "57 x 82 mm base, closed, cable coiled inside"),
              ("B  dish (v2, earlier draft)", "112 x 130 mm open tray, cable visible")]
    dr = ImageDraw.Draw(canvas)
    for i, im in enumerate(ims):
        canvas.paste(im, (x, 90))
        dr.text((x + 30, 12), labels[i][0], fill=(27, 31, 36), font=font)
        dr.text((x + 30, 52), labels[i][1], fill=(110, 115, 122), font=small)
        x += im.width
    canvas.save(os.path.join(IMG, "options_compact_vs_dish.png"))
    for s in shots:
        os.remove(s)
    print("renders written to", IMG)
