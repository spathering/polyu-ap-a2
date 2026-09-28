"""Application composition: load, prepare, render a still, then open the window."""

import os

from hk_weather.data.boundary import district_union, load_district_boundaries
from hk_weather.data.terrain import load_terrain
from hk_weather.data.weather import load_weather
from hk_weather.geometry.domain import prepare_geometry
from hk_weather.geometry.projection import MapProjection
from hk_weather.interaction.frame_controller import FrameController
from hk_weather.interaction.setup import attach_interactions
from hk_weather.output.screenshot import save_screenshot
from hk_weather.render.scene import build_scene


def load_project():
    """Load local source files and perform reusable geometric preparation."""
    weather = load_weather()
    terrain = load_terrain()
    districts = load_district_boundaries()
    prepared = prepare_geometry(
        weather, terrain, districts, district_union(districts), MapProjection()
    )
    return weather, prepared


def main():
    """Write the required still and open the autoplaying interactive 3D map."""
    weather, prepared = load_project()
    save_screenshot(weather, prepared)
    if os.environ.get("HK_WEATHER_NO_WINDOW") == "1":
        return

    handles = build_scene(prepared, off_screen=False)
    controller = FrameController(weather, prepared, handles)
    controller.apply(0)
    # Keep callback owners alive until Plotter.show() returns.
    interactions = attach_interactions(controller)
    handles.plotter.show(title="Hong Kong Weather Surfaces")
    return interactions
