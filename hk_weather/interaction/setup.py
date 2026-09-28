"""Attach interaction objects and retain them for the window lifetime."""

from dataclasses import dataclass

from hk_weather.interaction.camera_guard import CameraGuard
from hk_weather.interaction.cursor_probe import CursorProbe
from hk_weather.interaction.information import InformationPanel
from hk_weather.interaction.settings import SettingsPanel
from hk_weather.interaction.timeline import add_timeline


@dataclass
class InteractionHandles:
    timeline: object
    cursor: object
    camera: object
    settings: object
    information: object


def attach_interactions(controller):
    plotter = controller.handles.plotter
    timeline = add_timeline(plotter, controller, interactive=True)
    settings = SettingsPanel(plotter, timeline)
    information = InformationPanel(plotter)
    cursor = CursorProbe(controller)
    camera = CameraGuard(plotter)
    plotter.iren.add_observer("MouseMoveEvent", cursor.on_mouse_move)
    plotter.iren.add_observer("InteractionEvent", camera.enforce)
    plotter.add_timer_event(
        max_steps=10_000_000,
        duration=50,
        callback=cursor.pulse,
    )
    return InteractionHandles(timeline, cursor, camera, settings, information)
