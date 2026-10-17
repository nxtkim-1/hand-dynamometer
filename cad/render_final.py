"""render_final.py — renders of the final design. Run after dynamometer_cad.py."""
import os
import importlib.util
import cadquery as cq
import vtk

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("d", os.path.join(HERE, "dynamometer_cad.py"))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
OUT, TMP = d.OUT, os.path.join(d.OUT, "_render")
IMG = os.path.join(HERE, "..", "images")
os.makedirs(TMP, exist_ok=True); os.makedirs(IMG, exist_ok=True)

GREY, BLACK, TEAL = (0.88, 0.89, 0.91), (0.17, 0.18, 0.21), (0.18, 0.62, 0.54)
STEEL, MID, DARK = (0.62, 0.64, 0.68), (0.72, 0.60, 0.40), (0.30, 0.31, 0.34)


def export(name, part):
    path = os.path.join(TMP, f"{name}.stl")
    cq.exporters.export(part, path, tolerance=0.04, angularTolerance=0.15)
    return path


def actor(path, colour, offset=(0, 0, 0), opacity=1.0, edges=True):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(35); n.SplittingOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*offset)
    p = a.GetProperty(); p.SetColor(*colour); p.SetOpacity(opacity)
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.2); p.SetSpecularPower(30)
    acts = [a]
    if edges:
        fe = vtk.vtkFeatureEdges(); fe.SetInputConnection(r.GetOutputPort())
        fe.BoundaryEdgesOff(); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.SetFeatureAngle(40)
        em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort()); em.ScalarVisibilityOff()
        e = vtk.vtkActor(); e.SetMapper(em); e.SetPosition(*offset)
        e.GetProperty().SetColor(0.1, 0.1, 0.12); e.GetProperty().SetOpacity(0.45)
        acts.append(e)
    return acts


def render(groups, azim, elev, fname, zoom=0.95, size=1100):
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


palm, finger, cover, cell = d.palm(), d.finger(), d.cover(), d.cell()
P, F, C, L = export("palm", palm), export("finger", finger), export("cover", cover), export("cell", cell)

# assembled, from the finger side and the palm side
render([actor(P, GREY), actor(F, BLACK), actor(C, GREY)], 40, 12, "final_assembled.png")
render([actor(P, GREY), actor(F, BLACK), actor(C, GREY)], 220, 12, "final_assembled_back.png")

# exploded
render([actor(P, GREY, (-60, 0, 0)), actor(L, TEAL), actor(F, BLACK, (60, 0, 0)), actor(C, GREY, (0, 0, -45))],
       38, 14, "final_exploded.png", zoom=0.9)

# cut-away: everything sliced on the y = 0 plane
half = d.box(-80, 90, -80, 0, -60, 170)
Ps, Fs, Cs, Ls = (export(f"{n}_cut", p.intersect(half)) for n, p in
                  (("palm", palm), ("finger", finger), ("cover", cover), ("cell", cell)))
render([actor(Ps, GREY), actor(Fs, BLACK), actor(Cs, GREY), actor(Ls, TEAL)], 205, 8, "final_section.png")

# calibration: device palm-down in the cradle, clamped in a vise, mass on the dome hook
def to_rig(p):
    return p.rotate((0, 0, 0), (0, 1, 0), -90).rotate((0, 0, 0), (0, 0, 1), -90).translate((0, 50, 38))
Pr, Fr, Cr = (export(f"{n}_rig", to_rig(p)) for n, p in (("palm", palm), ("finger", finger), ("cover", cover)))
Cd = export("cradle", d.cradle().translate((0, 0, 0)))
hook_y, hook_z = d.HOOK_Z + 50, d.AX + 38
cord = export("cord", cq.Workplane("XY").workplane(offset=-70).center(0, hook_y).circle(1.2).extrude(hook_z + 70))
mass = export("mass", cq.Workplane("XY").workplane(offset=-110).center(0, hook_y).circle(22).extrude(40))
jaws = export("jaws", d.box(-58, -32, 45, 135, 0, 28).union(d.box(32, 58, 45, 135, 0, 28)))
render([actor(Cd, MID), actor(jaws, DARK), actor(Pr, GREY), actor(Fr, BLACK), actor(Cr, GREY),
        actor(cord, DARK, edges=False), actor(mass, STEEL)], 55, 18, "final_calibration.png", zoom=0.9)
print("renders written to", os.path.abspath(IMG))
