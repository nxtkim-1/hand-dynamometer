"""render_jamar.py — renders of the Jamar-style CONCEPT. Run after jamar_concept.py."""
import os
import cadquery as cq
import vtk
from PIL import Image, ImageDraw, ImageFont
import jamar_concept as J
import dynamometer_cad as D

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, "..", "images"))
TMP = os.path.join(D.OUT, "_render_jamar"); os.makedirs(TMP, exist_ok=True)
GREY, PALM, BLACK, TEAL, ORANGE, BLUE = (0.86, 0.87, 0.89), (0.74, 0.76, 0.80), (0.17, 0.18, 0.21), (0.18, 0.62, 0.54), (0.85, 0.42, 0.10), (0.25, 0.48, 0.85)


def export(name, part):
    p = os.path.join(TMP, f"{name}.stl"); cq.exporters.export(part, p, tolerance=0.04, angularTolerance=0.15); return p


def actor(path, col, op=1.0, edges=True):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(35); n.SplittingOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); pr = a.GetProperty(); pr.SetColor(*col); pr.SetOpacity(op)
    pr.SetAmbient(0.25); pr.SetDiffuse(0.75); pr.SetSpecular(0.2); pr.SetSpecularPower(30)
    out = [a]
    if edges:
        fe = vtk.vtkFeatureEdges(); fe.SetInputConnection(r.GetOutputPort())
        fe.BoundaryEdgesOff(); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.SetFeatureAngle(40)
        em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort()); em.ScalarVisibilityOff()
        e = vtk.vtkActor(); e.SetMapper(em); e.GetProperty().SetColor(0.1, 0.1, 0.12); e.GetProperty().SetOpacity(0.45 * op)
        out.append(e)
    return out


def render(groups, azim, elev, fname, focus, scale=None, zoom=1.0, size=1200):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for g in groups:
        for a in g:
            ren.AddActor(a)
    ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(40)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(size, size); win.AddRenderer(ren); win.SetAlphaBitPlanes(1); win.SetMultiSamples(0)
    cam = ren.GetActiveCamera(); cam.SetViewUp(0, 0, 1); cam.SetFocalPoint(*focus); cam.SetPosition(focus[0], focus[1] - 1, focus[2])
    ren.ResetCamera(); cam.Azimuth(azim); cam.Elevation(elev); cam.OrthogonalizeViewUp()
    if scale:
        cam.ParallelProjectionOn(); cam.SetFocalPoint(*focus); d = cam.GetDirectionOfProjection()
        cam.SetPosition(focus[0] - d[0] * 800, focus[1] - d[1] * 800, focus[2] - d[2] * 800); cam.SetParallelScale(scale); ren.ResetCameraClippingRange()
    else:
        ren.ResetCamera(); cam.Zoom(zoom)
    li = vtk.vtkLight(); li.SetLightTypeToCameraLight(); li.SetPosition(0.6, 0.8, 1); li.SetIntensity(0.9); ren.AddLight(li)
    win.Render(); w = vtk.vtkWindowToImageFilter(); w.SetInput(win); w.Update()
    out = os.path.join(IMG, fname); pw = vtk.vtkPNGWriter(); pw.SetFileName(out); pw.SetInputConnection(w.GetOutputPort()); pw.Write()
    return out


if __name__ == "__main__":
    fr, pb, fg, cv, cell = J.frame(), J.palm_bar(), J.finger(), J.cover(), D.cell()
    F, P, K, V, L = export("frame", fr), export("palm", pb), export("finger", fg), export("cover", cv), export("cell", cell)
    T, E = export("cable", J.cable_tube()), export("elec", J.electronics_zone())
    focus = ((J.ARM_X0 + J.BX1) / 2, 0, 50)
    render([actor(F, GREY), actor(P, PALM), actor(K, BLACK), actor(V, GREY)], -35, 18, "jamar_concept_view.png", focus, zoom=1.0)
    # cut-away on y = 0, seen from -y, parallel projection so it can be dimensioned
    half = D.box(-300, 300, 0, 300, -100, 300)
    Fs, Ps, Ks, Vs, Ls = (export(n + "_cut", p.intersect(half)) for n, p in (("frame", fr), ("palm", pb), ("finger", fg), ("cover", cv), ("cell", cell)))
    S = 132.0
    focus = (focus[0], 0, 44)
    side = render([actor(Fs, GREY), actor(Ps, PALM), actor(Ks, BLACK), actor(Vs, GREY), actor(Ls, TEAL),
                   actor(T, ORANGE), actor(E, BLUE, op=0.25, edges=False)], 0, 0, "jamar_concept_section.png", focus, scale=S)
    # annotate the section
    im = Image.open(side).convert("RGB"); W = im.width; k = (W / 2) / S
    px = lambda x, z: (W / 2 + (x - focus[0]) * k, W / 2 - (z - focus[2]) * k)
    dr = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype("DejaVuSans-Bold.ttf", 22); f2 = ImageFont.truetype("DejaVuSans.ttf", 19)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    def label(x, z, text, font=f2, fill=(27, 31, 36), anchor="mm"):
        dr.text(px(x, z), text, fill=fill, font=font, anchor=anchor)
    def hdim(x0, x1, z, text):
        a, b = px(x0, z), px(x1, z); dr.line([a, b], fill=(31, 78, 156), width=3)
        for p in (a, b): dr.line([(p[0], p[1] - 9), (p[0], p[1] + 9)], fill=(31, 78, 156), width=3)
        dr.text(((a[0] + b[0]) / 2, a[1] - 16), text, fill=(31, 78, 156), font=f2, anchor="mm")
    g = J.GAPS[J.POS]; xpb = J.FB_X0 - g
    hdim(xpb, J.FB_X0, 70, f"{g:.0f} mm")
    hdim(xpb - J.PB_T, J.FB_X1, 6, f"grip span {g + J.PB_T + J.FB_X1 - J.FB_X0:.0f} mm (position 2 of 5)")
    label(xpb - J.PB_T / 2, 158, "palm bar", f1); label((J.FB_X0 + J.FB_X1) / 2, 158, "finger bar", f1)
    label((J.BX0 + J.BX1) / 2, 158, "body", f1)
    label((J.FB_X0 + J.FB_X1) / 2, 70, "moves with", f2, (200, 200, 205)); label((J.FB_X0 + J.FB_X1) / 2, 64, "the cell top", f2, (200, 200, 205))
    label(11, -60, "electronics + spare cable (in the body)", f2, (40, 70, 140))
    label((xpb + J.FB_X0) / 2, 115, "hand", f2, (90, 95, 100)); label((xpb + J.FB_X0) / 2, 109, "goes in", f2, (90, 95, 100))
    dr.text((24, 20), "Jamar-style concept: cut through the middle", fill=(27, 31, 36), font=f1)
    dr.text((24, 52), "grey = fixed frame + palm bar   black = finger part   teal = load cell   orange = its cable", fill=(110, 115, 122), font=f2)
    im.save(side)
    print("renders written")
