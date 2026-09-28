"""Flat Y=0 land, sea and district-reference actors."""

import numpy as np
import pyvista as pv

from hk_weather.core.config import (
    DISTRICT_COLOUR,
    LAND_COLOUR,
    LAND_OPACITY,
    SEA_COLOUR,
    SEA_OPACITY,
)


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


def add_base_map(plotter, domain):
    """Add a translucent sea rectangle, land mesh and district lines."""
    sea_points = _points_at_y(domain.sea_corners_xz, 0.0)
    sea_faces = vtk_faces(np.asarray([[0, 1, 2], [0, 2, 3]], dtype=np.uint32))
    sea_mesh = pv.PolyData(sea_points, sea_faces)
    sea_actor = plotter.add_mesh(
        sea_mesh,
        color=SEA_COLOUR,
        opacity=SEA_OPACITY,
        ambient=1.0,
        diffuse=0.0,
        pickable=True,
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
    return sea_mesh, sea_actor, land_mesh, land_actor, district_mesh, district_actor
