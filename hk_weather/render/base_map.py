"""Flat Y=0 land, fading reference-grid and district actors."""

import numpy as np
import pyvista as pv

from hk_weather.core.config import (
    DISTRICT_COLOUR,
    GRID_EDGE_FADE_START,
    GRID_MAJOR_EVERY,
    GRID_MAJOR_OPACITY,
    GRID_MINOR_DIVISIONS,
    GRID_MINOR_OPACITY,
    LAND_COLOUR,
    LAND_OPACITY,
    SEA_COLOUR,
)
from hk_weather.render.fog import add_depth_fog


def vtk_faces(faces):
    return np.column_stack(
        (np.full(len(faces), 3, dtype=np.uint32), np.asarray(faces, dtype=np.uint32))
    ).ravel()


def _points_at_y(nodes_xz, y):
    return np.column_stack(
        (nodes_xz[:, 0], np.full(len(nodes_xz), y), nodes_xz[:, 1])
    )


def _district_mesh(lines_xz, y):
    points = []
    lines = []
    cursor = 0
    for line in lines_xz:
        if len(line) < 2:
            continue
        points.extend((float(x), float(y), float(z)) for x, z in line)
        lines.extend([len(line), *range(cursor, cursor + len(line))])
        cursor += len(line)
    mesh = pv.PolyData(np.asarray(points, dtype=float))
    mesh.lines = np.asarray(lines, dtype=np.int64)
    return mesh


def _grid_mesh(corners_xz, *, major):
    """Build major or minor lines with point alpha fading at the map edge."""
    corners = np.asarray(corners_xz, dtype=float)
    x_values = np.linspace(corners[:, 0].min(), corners[:, 0].max(), GRID_MINOR_DIVISIONS + 1)
    z_values = np.linspace(corners[:, 1].min(), corners[:, 1].max(), GRID_MINOR_DIVISIONS + 1)
    centre_x = 0.5 * (x_values[0] + x_values[-1])
    centre_z = 0.5 * (z_values[0] + z_values[-1])
    half_x = max(0.5 * (x_values[-1] - x_values[0]), 1.0)
    half_z = max(0.5 * (z_values[-1] - z_values[0]), 1.0)
    points = []
    lines = []
    alpha = []
    cursor = 0
    base_opacity = GRID_MAJOR_OPACITY if major else GRID_MINOR_OPACITY

    def add_line(samples):
        nonlocal cursor
        lines.extend([len(samples), *range(cursor, cursor + len(samples))])
        cursor += len(samples)
        for x, z in samples:
            radius = np.clip(
                np.hypot((x - centre_x) / half_x, (z - centre_z) / half_z),
                0.0,
                1.0,
            )
            fade_position = np.clip(
                (radius - GRID_EDGE_FADE_START) / (1.0 - GRID_EDGE_FADE_START), 0.0, 1.0
            )
            fade = 1.0 - fade_position * fade_position * (3.0 - 2.0 * fade_position)
            points.append((x, 0.0, z))
            alpha.append(round(255.0 * base_opacity * fade))

    for index, x in enumerate(x_values):
        if (index % GRID_MAJOR_EVERY == 0) == major:
            add_line([(x, z) for z in z_values])
    for index, z in enumerate(z_values):
        if (index % GRID_MAJOR_EVERY == 0) == major:
            add_line([(x, z) for x in x_values])

    mesh = pv.PolyData(np.asarray(points, dtype=float))
    mesh.lines = np.asarray(lines, dtype=np.int64)
    rgba = np.empty((len(points), 4), dtype=np.uint8)
    rgba[:, :3] = (128, 164, 172) if major else (88, 122, 130)
    rgba[:, 3] = np.asarray(alpha, dtype=np.uint8)
    mesh.point_data["grid_rgba"] = rgba
    return mesh


def add_base_map(plotter, domain):
    """Add an invisible pick plane, fading grid, land and district lines."""
    sea_points = _points_at_y(domain.sea_corners_xz, 0.0)
    sea_faces = vtk_faces(np.asarray([[0, 1, 2], [0, 2, 3]], dtype=np.uint32))
    pick_plane_mesh = pv.PolyData(sea_points, sea_faces)
    pick_plane_actor = plotter.add_mesh(
        pick_plane_mesh,
        color=SEA_COLOUR,
        opacity=0.0,
        ambient=1.0,
        diffuse=0.0,
        pickable=True,
        show_scalar_bar=False,
    )

    grid_minor_mesh = _grid_mesh(domain.sea_corners_xz, major=False)
    grid_minor_actor = plotter.add_mesh(
        grid_minor_mesh,
        scalars="grid_rgba",
        rgba=True,
        line_width=1.0,
        ambient=1.0,
        diffuse=0.0,
        pickable=False,
        show_scalar_bar=False,
    )
    grid_major_mesh = _grid_mesh(domain.sea_corners_xz, major=True)
    grid_major_actor = plotter.add_mesh(
        grid_major_mesh,
        scalars="grid_rgba",
        rgba=True,
        line_width=1.8,
        ambient=1.0,
        diffuse=0.0,
        pickable=False,
        show_scalar_bar=False,
    )

    land_mesh = pv.PolyData(
        _points_at_y(domain.nodes_xz, 0.0), vtk_faces(domain.faces)
    )
    land_actor = plotter.add_mesh(
        land_mesh,
        color=LAND_COLOUR,
        opacity=LAND_OPACITY,
        ambient=1.0,
        diffuse=0.0,
        pickable=True,
        show_scalar_bar=False,
    )

    line_y = domain.horizontal_span_m * 0.00045
    district_mesh = _district_mesh(domain.district_lines_xz, line_y)
    district_actor = plotter.add_mesh(
        district_mesh,
        color=DISTRICT_COLOUR,
        opacity=0.72,
        line_width=1.2,
        ambient=1.0,
        pickable=False,
        show_scalar_bar=False,
    )
    for actor in (grid_minor_actor, grid_major_actor, land_actor, district_actor):
        add_depth_fog(actor)
    return (
        pick_plane_mesh,
        pick_plane_actor,
        grid_minor_mesh,
        grid_minor_actor,
        grid_major_mesh,
        grid_major_actor,
        land_mesh,
        land_actor,
        district_mesh,
        district_actor,
    )
