"""The single dual-surface scene factory for screenshots and interaction."""

from dataclasses import dataclass
import math

import pyvista as pv

from hk_weather.core.config import (
    BACKGROUND_COLOUR,
    BACKGROUND_TOP_COLOUR,
    CAMERA_DISTANCE_FACTOR,
    INITIAL_CAMERA_PITCH_DEG,
)
from hk_weather.render.base_map import add_base_map
from hk_weather.render.field_surfaces import add_field_surfaces
from hk_weather.render.station_links import add_station_links
from hk_weather.render.text import add_cursor_text, add_date_text, add_surface_note


@dataclass
class SceneHandles:
    plotter: object
    pick_plane_mesh: object
    pick_plane_actor: object
    grid_minor_mesh: object
    grid_minor_actor: object
    grid_major_mesh: object
    grid_major_actor: object
    land_mesh: object
    land_actor: object
    district_mesh: object
    district_actor: object
    temperature_mesh: object
    temperature_actor: object
    rainfall_mesh: object
    rainfall_actor: object
    station_link_mesh: object
    station_link_actor: object
    station_endpoint_mesh: object
    station_endpoint_actor: object
    highlight_mesh: object
    highlight_actor: object
    highlight_points_mesh: object
    highlight_points_actor: object
    date_actor: object
    cursor_actor: object
    surface_note_actor: object


def set_initial_camera(plotter, horizontal_span_m):
    """Set a stable Y-up oblique view that reveals both surfaces."""
    distance = horizontal_span_m * CAMERA_DISTANCE_FACTOR
    pitch = math.radians(INITIAL_CAMERA_PITCH_DEG)
    horizontal = distance * math.cos(pitch)
    vertical = distance * math.sin(pitch)
    diagonal = horizontal / math.sqrt(2.0)
    focal = (0.0, 0.0, 0.0)
    position = (-diagonal, vertical, -diagonal)
    plotter.camera_position = [position, focal, (0.0, 1.0, 0.0)]
    plotter.camera.zoom(1.04)


def build_scene(prepared, off_screen=False, window_size=(1280, 820)):
    """Create persistent actors; frame changes only mutate their arrays."""
    plotter = pv.Plotter(off_screen=off_screen, window_size=window_size)
    plotter.set_background(BACKGROUND_COLOUR, top=BACKGROUND_TOP_COLOUR)
    base = add_base_map(plotter, prepared.domain)
    surfaces = add_field_surfaces(plotter, prepared)
    stations = add_station_links(plotter, prepared.domain, prepared.frames)
    date_actor = add_date_text(plotter)
    cursor_actor = add_cursor_text(plotter)
    surface_note_actor = add_surface_note(plotter)
    set_initial_camera(plotter, prepared.domain.horizontal_span_m)
    plotter.enable_anti_aliasing("ssaa")
    try:
        plotter.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
    except (AttributeError, RuntimeError):
        pass
    return SceneHandles(
        plotter=plotter,
        pick_plane_mesh=base[0],
        pick_plane_actor=base[1],
        grid_minor_mesh=base[2],
        grid_minor_actor=base[3],
        grid_major_mesh=base[4],
        grid_major_actor=base[5],
        land_mesh=base[6],
        land_actor=base[7],
        district_mesh=base[8],
        district_actor=base[9],
        temperature_mesh=surfaces[0],
        temperature_actor=surfaces[1],
        rainfall_mesh=surfaces[2],
        rainfall_actor=surfaces[3],
        station_link_mesh=stations[0],
        station_link_actor=stations[1],
        station_endpoint_mesh=stations[2],
        station_endpoint_actor=stations[3],
        highlight_mesh=stations[4],
        highlight_actor=stations[5],
        highlight_points_mesh=stations[6],
        highlight_points_actor=stations[7],
        date_actor=date_actor,
        cursor_actor=cursor_actor,
        surface_note_actor=surface_note_actor,
    )
