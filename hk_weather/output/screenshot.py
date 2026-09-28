"""Render the required README still without creating a second visualisation path."""

from hk_weather.core.config import SCREENSHOT_DAY_INDEX
from hk_weather.core.paths import OUT
from hk_weather.interaction.frame_controller import FrameController
from hk_weather.interaction.timeline import add_timeline
from hk_weather.render.scene import build_scene


PICTURE = OUT / "hong-kong-weather-april.png"


def save_screenshot(weather, prepared, path=PICTURE):
    """Save the 24 April showcase frame from the normal scene builder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handles = build_scene(prepared, off_screen=True)
    controller = FrameController(weather, prepared, handles)
    controller.apply(SCREENSHOT_DAY_INDEX)
    add_timeline(handles.plotter, controller, interactive=False)
    handles.plotter.show(screenshot=str(path), auto_close=True)
    print(f"wrote {path.relative_to(OUT.parent)}")
    return path
