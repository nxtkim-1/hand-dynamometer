"""render_dish.py — renders of the DRAFT dish base. Run after dish_base_draft.py (needs cadquery + vtk)."""
import os
import cadquery as cq
import vtk
import dynamometer_cad as D
import dish_base_draft as B

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
TMP = os.path.join(D.OUT, "_render_dish")
os.makedirs(TMP, exist_ok=True)
GREY, BLACK, TEAL, ORANGE = (0.88, 0.89, 0.91), (0.17, 0.18, 0.21), (0.18, 0.62, 0.54), (0.90, 0.42, 0.10)


def export(name, part):
    path = os.path.join(TMP, f"{name}.stl")
    cq.exporters.export(part, path, tolerance=0.05, angularTolerance=0.2)
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
        e.GetProperty().SetColor(0.1, 0.1, 0.12); e.GetProperty().SetOpacity(0.45)
        acts.append(e)
    return acts


def render(groups, azim, elev, fname, zoom=0.95, size=1200):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for g in groups:
        for a in g:
            ren.AddActor(a)
    ren.SetUseDepthPeeling(1)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(size, size); win.AddRenderer(ren)
    cam = ren.GetActiveCamera(); cam.SetViewUp(0, 0, 1); cam.SetPosition(0, -1, 0); cam.SetFocalPoint(0, 0, 0)
    ren.ResetCamera(); cam.Azimuth(azim); cam.Elevation(elev); cam.OrthogonalizeViewUp()
    ren.ResetCamera(); cam.Zoom(zoom)
    li = vtk.vtkLight(); li.SetLightTypeToCameraLight(); li.SetPosition(0.6, 0.8, 1); li.SetIntensity(0.9); ren.AddLight(li)
    win.Render()
    w = vtk.vtkWindowToImageFilter(); w.SetInput(win); w.Update()
    pw = vtk.vtkPNGWriter(); pw.SetFileName(os.path.join(IMG, fname)); pw.SetInputConnection(w.GetOutputPort()); pw.Write()


pm, fg, pl, ce, cb = B.palm_dish(), B.finger_dish(), B.plug(), D.cell(), B.cable_tube()
P, F, C, L, K = (export(n, p) for n, p in (("palm", pm), ("finger", fg), ("plug", pl), ("cell", ce), ("cable", cb)))
grp = [actor(P, GREY), actor(F, BLACK), actor(C, GREY), actor(L, TEAL), actor(K, ORANGE, edges=False)]
render(grp, 145, 28, "dish_draft_v2_assembled.png", zoom=1.0)
render(grp, 90, 8, "dish_draft_v2_side.png", zoom=1.0)

# section through the cable's own plane (x = cable centre), looking from +x
half = D.box(-90, B.CXC, -90, 90, -60, 170)
Ps, Fs, Cs, Ls = (export(n + "_cut", p.intersect(half)) for n, p in (("palm", pm), ("finger", fg), ("plug", pl), ("cell", ce)))
Ks = export("cable_cut", cb.intersect(half))
render([actor(Ps, GREY), actor(Fs, BLACK), actor(Cs, GREY), actor(Ls, TEAL), actor(Ks, ORANGE, edges=False)], 90, 0,
       "dish_draft_v2_section.png", zoom=0.95)
print("renders written to", os.path.abspath(IMG))
