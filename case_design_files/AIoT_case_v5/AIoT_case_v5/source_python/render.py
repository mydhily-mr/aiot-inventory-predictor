"""Off-screen VTK renderer for quick visual checks of the STL files."""
import vtk, sys, os, math

DARK = (0.23, 0.25, 0.28)
BLUE = (0.10, 0.45, 0.85)


def load(path, color, opacity=1.0, translate=(0, 0, 0), clip=None, rotate=None):
    r = vtk.vtkSTLReader(); r.SetFileName(path); r.Update()
    src = r.GetOutputPort()
    tf = vtk.vtkTransform()
    tf.Translate(*translate)
    if rotate:
        for ax, ang in rotate:
            getattr(tf, "Rotate" + ax.upper())(ang)
    f = vtk.vtkTransformPolyDataFilter(); f.SetTransform(tf); f.SetInputConnection(src); f.Update()
    port = f.GetOutputPort()
    if clip is not None:
        plane = vtk.vtkPlane(); plane.SetOrigin(*clip[0]); plane.SetNormal(*clip[1])
        c = vtk.vtkClipPolyData(); c.SetClipFunction(plane); c.SetInputConnection(port); c.Update()
        port = c.GetOutputPort()
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(port); n.SetFeatureAngle(35); n.Update()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*color); p.SetOpacity(opacity)
    p.SetSpecular(0.25); p.SetSpecularPower(20); p.SetAmbient(0.18); p.SetDiffuse(0.85)
    return a


def render(actors, out, pos, focal, up=(0, 0, 1), size=(1100, 900), parallel=False, scale=None, title=None):
    ren = vtk.vtkRenderer(); ren.SetBackground(0.96, 0.96, 0.97); ren.SetBackground2(0.82, 0.84, 0.88)
    ren.GradientBackgroundOn()
    for a in actors:
        ren.AddActor(a)
    cam = ren.GetActiveCamera(); cam.SetPosition(*pos); cam.SetFocalPoint(*focal); cam.SetViewUp(*up)
    if parallel:
        cam.ParallelProjectionOn()
        if scale: cam.SetParallelScale(scale)
    ren.ResetCameraClippingRange()
    if not parallel:
        ren.ResetCamera(); cam.Zoom(1.25)
    if title:
        t = vtk.vtkTextActor(); t.SetInput(title); t.GetTextProperty().SetFontSize(24)
        t.GetTextProperty().SetColor(0.1, 0.1, 0.1); t.SetPosition(15, size[1] - 40); ren.AddActor2D(t)
    lk = vtk.vtkLightKit(); lk.AddLightsToRenderer(ren)
    w = vtk.vtkRenderWindow(); w.SetOffScreenRendering(1); w.AddRenderer(ren); w.SetSize(*size)
    w.SetMultiSamples(8)
    w.Render()
    f = vtk.vtkWindowToImageFilter(); f.SetInput(w); f.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(out); wr.SetInputConnection(f.GetOutputPort()); wr.Write()
