"""Screen-space date and cursor-following information text."""

from vtkmodules.vtkRenderingCore import vtkTextActor


def _text_actor(font_size, background_opacity=0.0):
    actor = vtkTextActor()
    style = actor.GetTextProperty()
    style.SetFontFamilyToArial()
    style.SetFontSize(font_size)
    style.SetColor(0.91, 0.97, 0.98)
    style.SetBold(True)
    style.SetBackgroundColor(0.025, 0.08, 0.105)
    style.SetBackgroundOpacity(background_opacity)
    style.SetFrame(False)
    return actor


def add_date_text(plotter):
    actor = _text_actor(22, 0.66)
    actor.SetInput("")
    actor.SetDisplayPosition(28, plotter.window_size[1] - 52)
    plotter.renderer.AddViewProp(actor)
    return actor


def add_cursor_text(plotter):
    actor = _text_actor(15, 0.82)
    actor.SetInput("")
    actor.SetVisibility(False)
    plotter.renderer.AddViewProp(actor)
    return actor


def add_surface_note(plotter):
    actor = _text_actor(13, 0.55)
    actor.SetInput(
        "TEMPERATURE ABOVE · RAINFALL BELOW\n"
        "Baseline plane Y = 0 · spatial and between-day values are estimates"
    )
    actor.SetDisplayPosition(28, 30)
    plotter.renderer.AddViewProp(actor)
    return actor
