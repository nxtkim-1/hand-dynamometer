"""render_design_a.py — proper 3D renders of Design A using VTK (off-screen)."""
import os
import vtk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output_proto1b")
IMG = os.path.join(HERE, "..", "images", "prototypes")
os.makedirs(IMG, exist_ok=True)

COL = {"palm": (0.88, 0.89, 0.91), "cover": (0.88, 0.89, 0.91),
       "finger": (0.17, 0.18, 0.21), "cell": (0.18, 0.62, 0.54)}


def actor(name, offset=(0, 0, 0), opacity=1.0):
    r = vtk.vtkSTLReader(); r.SetFileName(os.path.join(OUT, f"{name}.stl"))
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort())
    n.SetFeatureAngle(35); n.SplittingOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*offset)
    p = a.GetProperty(); p.SetColor(*COL[name]); p.SetOpacity(opacity)
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.18); p.SetSpecularPower(25)
    # crisp feature edges so the form reads clearly
    fe = vtk.vtkFeatureEdges(); fe.SetInputConnection(r.GetOutputPort())
    fe.BoundaryEdgesOff(); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.FeatureEdgesOn()
    fe.SetFeatureAngle(40)
    em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort()); em.ScalarVisibilityOff()
    e = vtk.vtkActor(); e.SetMapper(em); e.SetPosition(*offset)
    e.GetProperty().SetColor(0.12, 0.12, 0.14); e.GetProperty().SetLineWidth(1.2)
    e.GetProperty().SetOpacity(0.55 if opacity == 1 else 0.25)
    return [a, e]


def render(items, azim, elev, fname, zoom=0.95):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for acts in items:
        for a in acts:
            ren.AddActor(a)
    ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(8)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(1100, 1100)
    win.SetAlphaBitPlanes(1); win.SetMultiSamples(0); win.AddRenderer(ren)
    cam = ren.GetActiveCamera()
    cam.SetViewUp(0, 0, 1); cam.SetPosition(0, -1, 0); cam.SetFocalPoint(0, 0, 0)
    ren.ResetCamera(); cam.Azimuth(azim); cam.Elevation(elev); cam.OrthogonalizeViewUp()
    ren.ResetCamera(); cam.Zoom(zoom)
    light = vtk.vtkLight(); light.SetLightTypeToCameraLight(); light.SetPosition(0.6, 0.8, 1); light.SetIntensity(0.9)
    ren.AddLight(light)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(os.path.join(IMG, fname))
    wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()


render([actor("palm", (-55, 0, 0)), actor("cell"), actor("finger", (55, 0, 0)), actor("cover", (0, 0, -40))],
       38, 14, "proto1b_sculpted_exploded.png", zoom=0.9)
print("ok")
