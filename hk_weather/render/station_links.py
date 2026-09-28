"""Dynamic station links, endpoints and one reusable highlight."""

import numpy as np
import pyvista as pv

from hk_weather.core.config import HIGHLIGHT_COLOUR, STATION_COLOUR


def station_link_points(station_xz, temperature_y, rainfall_y):
    points = np.empty((len(station_xz) * 3, 3), dtype=float)
    for index, (x, z) in enumerate(station_xz):
        offset = index * 3
        points[offset] = (x, temperature_y[index], z)
        points[offset + 1] = (x, 0.0, z)
        points[offset + 2] = (x, rainfall_y[index], z)
    return points


def _link_cells(station_count):
    values = []
    for index in range(station_count):
        start = index * 3
        values.extend((3, start, start + 1, start + 2))
    return np.asarray(values, dtype=np.int64)


def add_station_links(plotter, domain, frames):
    station_ids = domain.station_node_ids
    points = station_link_points(
        domain.station_xz,
        frames.temperature_y[0, station_ids],
        frames.rainfall_y[0, station_ids],
    )
    link_mesh = pv.PolyData(points)
    link_mesh.lines = _link_cells(len(domain.station_xz))
    link_actor = plotter.add_mesh(
        link_mesh,
        color=STATION_COLOUR,
        opacity=0.62,
        line_width=1.3,
        ambient=1.0,
        pickable=False,
        show_scalar_bar=False,
    )

    endpoint_ids = np.asarray(
        [index * 3 + endpoint for index in range(len(domain.station_xz)) for endpoint in (0, 2)]
    )
    endpoint_mesh = pv.PolyData(points[endpoint_ids])
    endpoint_actor = plotter.add_mesh(
        endpoint_mesh,
        color=STATION_COLOUR,
        point_size=8,
        render_points_as_spheres=True,
        emissive=True,
        pickable=False,
        show_scalar_bar=False,
    )

    highlight_mesh = pv.PolyData(points[:3].copy())
    highlight_mesh.lines = np.asarray([3, 0, 1, 2], dtype=np.int64)
    highlight_actor = plotter.add_mesh(
        highlight_mesh,
        color=HIGHLIGHT_COLOUR,
        line_width=4,
        opacity=0.96,
        ambient=1.0,
        pickable=False,
        show_scalar_bar=False,
    )
    highlight_actor.visibility = False

    highlight_points = pv.PolyData(points[[0, 2]].copy())
    highlight_points_actor = plotter.add_mesh(
        highlight_points,
        color=HIGHLIGHT_COLOUR,
        point_size=15,
        render_points_as_spheres=True,
        emissive=True,
        pickable=False,
        show_scalar_bar=False,
    )
    highlight_points_actor.visibility = False
    return (
        link_mesh,
        link_actor,
        endpoint_mesh,
        endpoint_actor,
        highlight_mesh,
        highlight_actor,
        highlight_points,
        highlight_points_actor,
    )
