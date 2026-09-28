"""Temperature and rainfall surface actor construction."""

import numpy as np
import pyvista as pv

from hk_weather.core.config import (
    RAINFALL_BASELINE_MM,
    RAINFALL_COLOURS,
    RAINFALL_FADE_WIDTH_MM,
    RAINFALL_OPACITY,
    RAINFALL_RANGE_MM,
    TEMPERATURE_FADE_BASELINE_C,
    TEMPERATURE_COLOURS,
    TEMPERATURE_FADE_WIDTH_C,
    TEMPERATURE_OPACITY,
    TEMPERATURE_RANGE_C,
)
from hk_weather.render.base_map import vtk_faces
from hk_weather.render.fog import add_depth_fog


def _points(nodes_xz, y):
    return np.column_stack((nodes_xz[:, 0], y, nodes_xz[:, 1]))


def _rgb(colour):
    value = colour.lstrip("#")
    return np.asarray(
        [int(value[index : index + 2], 16) for index in (0, 2, 4)], dtype=float
    )


def _fading_lookup_table(colours, value_range, baseline, fade_width, max_opacity):
    """Create colour plus smooth baseline-distance alpha in one VTK lookup table."""
    count = 256
    palette = np.asarray([_rgb(colour) for colour in colours])
    palette_position = np.linspace(0.0, 1.0, len(palette))
    target_position = np.linspace(0.0, 1.0, count)
    rgba = np.empty((count, 4), dtype=np.uint8)
    for channel in range(3):
        rgba[:, channel] = np.round(
            np.interp(target_position, palette_position, palette[:, channel])
        ).astype(np.uint8)
    values = np.linspace(value_range[0], value_range[1], count)
    distance = np.clip(np.abs(values - baseline) / fade_width, 0.0, 1.0)
    smooth = distance * distance * (3.0 - 2.0 * distance)
    rgba[:, 3] = np.round(255.0 * max_opacity * smooth).astype(np.uint8)
    table = pv.LookupTable()
    table.values = rgba
    table.scalar_range = value_range
    return table


def add_field_surfaces(plotter, prepared):
    domain = prepared.domain
    frames = prepared.frames
    temperature_mesh = pv.PolyData(
        _points(domain.nodes_xz, frames.temperature_y[0]), vtk_faces(domain.faces)
    )
    temperature_mesh.point_data["temperature_c"] = frames.temperature_c[0]
    temperature_lut = _fading_lookup_table(
        TEMPERATURE_COLOURS,
        TEMPERATURE_RANGE_C,
        TEMPERATURE_FADE_BASELINE_C,
        TEMPERATURE_FADE_WIDTH_C,
        TEMPERATURE_OPACITY,
    )
    temperature_actor = plotter.add_mesh(
        temperature_mesh,
        scalars="temperature_c",
        cmap=temperature_lut,
        clim=TEMPERATURE_RANGE_C,
        smooth_shading=True,
        ambient=0.34,
        diffuse=0.72,
        specular=0.12,
        pickable=False,
        show_edges=False,
        scalar_bar_args={
            "title": "Temperature (°C)",
            "vertical": True,
            "position_x": 0.87,
            "position_y": 0.12,
            "height": 0.30,
            "width": 0.055,
            "title_font_size": 12,
            "label_font_size": 10,
            "color": "#e9f5f7",
            "fmt": "%.0f",
        },
    )

    rainfall_mesh = pv.PolyData(
        _points(domain.nodes_xz, frames.rainfall_y[0]), vtk_faces(domain.faces)
    )
    rainfall_mesh.point_data["rainfall_mm"] = frames.rainfall_mm[0]
    rainfall_lut = _fading_lookup_table(
        RAINFALL_COLOURS,
        RAINFALL_RANGE_MM,
        RAINFALL_BASELINE_MM,
        RAINFALL_FADE_WIDTH_MM,
        RAINFALL_OPACITY,
    )
    rainfall_actor = plotter.add_mesh(
        rainfall_mesh,
        scalars="rainfall_mm",
        cmap=rainfall_lut,
        clim=RAINFALL_RANGE_MM,
        smooth_shading=True,
        ambient=0.34,
        diffuse=0.72,
        specular=0.08,
        pickable=False,
        show_edges=False,
        culling=False,
        scalar_bar_args={
            "title": "Rainfall height (mm)",
            "vertical": True,
            "position_x": 0.87,
            "position_y": 0.53,
            "height": 0.34,
            "width": 0.055,
            "title_font_size": 12,
            "label_font_size": 10,
            "color": "#e9f5f7",
            "fmt": "%.0f",
        },
    )
    add_depth_fog(temperature_actor)
    add_depth_fog(rainfall_actor)
    return temperature_mesh, temperature_actor, rainfall_mesh, rainfall_actor
