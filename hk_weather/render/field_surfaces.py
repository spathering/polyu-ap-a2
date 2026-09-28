"""Temperature and rainfall surface actor construction."""

import numpy as np
import pyvista as pv

from hk_weather.core.config import (
    RAINFALL_COLOURS,
    RAINFALL_OPACITY,
    RAINFALL_RANGE_MM,
    TEMPERATURE_COLOURS,
    TEMPERATURE_OPACITY,
    TEMPERATURE_RANGE_C,
)
from hk_weather.render.base_map import vtk_faces


def _points(nodes_xz, y):
    return np.column_stack((nodes_xz[:, 0], y, nodes_xz[:, 1]))


def add_field_surfaces(plotter, prepared):
    domain = prepared.domain
    frames = prepared.frames
    temperature_mesh = pv.PolyData(
        _points(domain.nodes_xz, frames.temperature_y[0]), vtk_faces(domain.faces)
    )
    temperature_mesh.point_data["temperature_c"] = frames.temperature_c[0]
    temperature_actor = plotter.add_mesh(
        temperature_mesh,
        scalars="temperature_c",
        cmap=TEMPERATURE_COLOURS,
        clim=TEMPERATURE_RANGE_C,
        opacity=TEMPERATURE_OPACITY,
        smooth_shading=True,
        ambient=0.34,
        diffuse=0.72,
        specular=0.12,
        pickable=False,
        show_edges=False,
        scalar_bar_args={
            "title": "Temperature height (°C)",
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

    rainfall_mesh = pv.PolyData(
        _points(domain.nodes_xz, frames.rainfall_y[0]), vtk_faces(domain.faces)
    )
    rainfall_mesh.point_data["rainfall_mm"] = frames.rainfall_mm[0]
    rainfall_actor = plotter.add_mesh(
        rainfall_mesh,
        scalars="rainfall_mm",
        cmap=RAINFALL_COLOURS,
        clim=RAINFALL_RANGE_MM,
        opacity=RAINFALL_OPACITY,
        smooth_shading=True,
        ambient=0.34,
        diffuse=0.72,
        specular=0.08,
        pickable=False,
        show_edges=False,
        culling=False,
        scalar_bar_args={
            "title": "Rainfall depth (mm)",
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
    return temperature_mesh, temperature_actor, rainfall_mesh, rainfall_actor
