"""Build the flat station-aware map topology and all interpolated frames."""

import numpy as np
from shapely import contains_xy

from hk_weather.core.config import (
    DOMAIN_STRIDE,
    LAND_THRESHOLD_M,
    RAINFALL_IDW_NEIGHBOURS,
    RAINFALL_IDW_POWER,
    TEMPERATURE_IDW_NEIGHBOURS,
    TEMPERATURE_IDW_POWER,
)
from hk_weather.core.models import FieldFrames, MapDomain, PreparedGeometry
from hk_weather.geometry.height_mapping import rainfall_to_y, temperature_to_y
from hk_weather.geometry.interpolation import interpolate_fields, inverse_distance_weights


def _geometry_lines(geometry):
    """Yield exterior and interior rings from polygonal geometry."""
    if geometry.geom_type == "Polygon":
        yield geometry.exterior
        yield from geometry.interiors
    elif geometry.geom_type == "MultiPolygon":
        for polygon in geometry.geoms:
            yield polygon.exterior
            yield from polygon.interiors


def _station_grid_ids(x_grid, z_grid, station_xz):
    """Assign every station a distinct nearest raster vertex."""
    flat = np.column_stack((x_grid.ravel(), z_grid.ravel()))
    selected = []
    occupied = set()
    for station in station_xz:
        order = np.argsort(np.sum((flat - station) ** 2, axis=1))
        grid_id = next(int(value) for value in order if int(value) not in occupied)
        occupied.add(grid_id)
        selected.append(grid_id)
    return np.asarray(selected, dtype=np.int64)


def _grid_faces(x_grid, z_grid, land_mask, territory):
    rows, columns = x_grid.shape
    point_ids = np.arange(rows * columns, dtype=np.int64).reshape(rows, columns)
    centres_x = (
        x_grid[:-1, :-1] + x_grid[:-1, 1:] + x_grid[1:, 1:] + x_grid[1:, :-1]
    ) / 4.0
    centres_z = (
        z_grid[:-1, :-1] + z_grid[:-1, 1:] + z_grid[1:, 1:] + z_grid[1:, :-1]
    ) / 4.0
    land_count = (
        land_mask[:-1, :-1].astype(np.int8)
        + land_mask[:-1, 1:]
        + land_mask[1:, 1:]
        + land_mask[1:, :-1]
    )
    cell_width = float(np.median(np.abs(np.diff(x_grid, axis=1))))
    inside = contains_xy(territory.buffer(cell_width * 0.55), centres_x, centres_z)
    keep = inside & (land_count >= 3)

    top_left = point_ids[:-1, :-1][keep]
    top_right = point_ids[:-1, 1:][keep]
    bottom_right = point_ids[1:, 1:][keep]
    bottom_left = point_ids[1:, :-1][keep]
    return np.concatenate(
        (
            np.column_stack((top_left, top_right, bottom_right)),
            np.column_stack((top_left, bottom_right, bottom_left)),
        ),
        axis=0,
    )


def _force_station_neighbourhoods(mask, station_ids):
    rows, columns = mask.shape
    for grid_id in station_ids:
        row, column = divmod(int(grid_id), columns)
        row_a, row_b = max(0, row - 1), min(rows, row + 2)
        col_a, col_b = max(0, column - 1), min(columns, column + 2)
        mask[row_a:row_b, col_a:col_b] = True


def _compact_topology(x_grid, z_grid, faces, station_grid_ids):
    used = np.unique(faces)
    missing = sorted(set(station_grid_ids.tolist()) - set(used.tolist()))
    if missing:
        raise RuntimeError(f"station nodes are not referenced by surface faces: {missing}")
    remap = np.full(x_grid.size, -1, dtype=np.int64)
    remap[used] = np.arange(len(used), dtype=np.int64)
    nodes = np.column_stack((x_grid.ravel()[used], z_grid.ravel()[used]))
    return nodes, remap[faces], remap[station_grid_ids]


def _project_district_lines(districts, projection, origin_x, origin_z):
    lines = []
    for district in districts:
        projected = projection.geometry(district.geometry).simplify(55.0)
        for ring in _geometry_lines(projected):
            coordinates = np.asarray(ring.coords, dtype=np.float32)
            if len(coordinates) >= 2:
                coordinates[:, 0] -= origin_x
                coordinates[:, 1] -= origin_z
                lines.append(coordinates[:, :2])
    return tuple(lines)


def prepare_geometry(weather, terrain, districts, territory, projection):
    """Prepare a flat base, exact station nodes and 30 dual-surface frames."""
    source_longitudes = terrain.longitudes[::DOMAIN_STRIDE]
    source_latitudes = terrain.latitudes[::DOMAIN_STRIDE]
    source_elevations = terrain.elevations_m[::DOMAIN_STRIDE, ::DOMAIN_STRIDE]
    longitude_grid, latitude_grid = np.meshgrid(source_longitudes, source_latitudes)
    x_grid, z_grid = projection.points(longitude_grid, latitude_grid)
    projected_territory = projection.geometry(territory)

    station_x, station_z = projection.points(weather.longitudes, weather.latitudes)
    station_xz_raw = np.column_stack((station_x, station_z))
    station_grid_ids = _station_grid_ids(x_grid, z_grid, station_xz_raw)
    x_flat = x_grid.ravel()
    z_flat = z_grid.ravel()
    x_flat[station_grid_ids] = station_x
    z_flat[station_grid_ids] = station_z
    x_grid = x_flat.reshape(x_grid.shape)
    z_grid = z_flat.reshape(z_grid.shape)

    land_mask = source_elevations > LAND_THRESHOLD_M
    territory_mask = contains_xy(projected_territory, x_grid, z_grid)
    land_mask &= territory_mask
    _force_station_neighbourhoods(land_mask, station_grid_ids)
    faces = _grid_faces(x_grid, z_grid, land_mask, projected_territory)
    nodes_raw, compact_faces, station_node_ids = _compact_topology(
        x_grid, z_grid, faces, station_grid_ids
    )

    min_x, min_z = float(np.min(x_grid)), float(np.min(z_grid))
    max_x, max_z = float(np.max(x_grid)), float(np.max(z_grid))
    origin_x = (min_x + max_x) / 2.0
    origin_z = (min_z + max_z) / 2.0
    nodes_xz = nodes_raw - np.array([origin_x, origin_z])
    station_xz = station_xz_raw - np.array([origin_x, origin_z])
    nodes_xz[station_node_ids] = station_xz
    horizontal_span = max(max_x - min_x, max_z - min_z)

    temperature_weights = inverse_distance_weights(
        nodes_xz,
        station_xz,
        power=TEMPERATURE_IDW_POWER,
        neighbours=TEMPERATURE_IDW_NEIGHBOURS,
    )
    rainfall_weights = inverse_distance_weights(
        nodes_xz,
        station_xz,
        power=RAINFALL_IDW_POWER,
        neighbours=RAINFALL_IDW_NEIGHBOURS,
    )
    temperature_fields = interpolate_fields(
        temperature_weights, weather.temperatures_c, transform="identity"
    )
    rainfall_fields = interpolate_fields(
        rainfall_weights, weather.rainfall_mm, transform="log1p"
    )
    temperature_fields[:, station_node_ids] = weather.temperatures_c
    rainfall_fields[:, station_node_ids] = weather.rainfall_mm

    frames = FieldFrames(
        temperature_c=np.asarray(temperature_fields, dtype=np.float32),
        rainfall_mm=np.asarray(rainfall_fields, dtype=np.float32),
        temperature_y=np.asarray(
            temperature_to_y(temperature_fields, horizontal_span), dtype=np.float32
        ),
        rainfall_y=np.asarray(
            rainfall_to_y(rainfall_fields, horizontal_span), dtype=np.float32
        ),
    )
    if not np.all(frames.temperature_y > 0.0):
        raise RuntimeError("temperature surface must stay above Y=0")
    if not np.all(frames.rainfall_y <= 1e-7):
        raise RuntimeError("rainfall surface must stay at or below Y=0")
    if not np.allclose(
        frames.temperature_c[:, station_node_ids], weather.temperatures_c, atol=1e-5
    ) or not np.allclose(
        frames.rainfall_mm[:, station_node_ids], weather.rainfall_mm, atol=1e-5
    ):
        raise RuntimeError("surface fields do not hit exact station observations")

    domain = MapDomain(
        nodes_xz=np.asarray(nodes_xz, dtype=np.float32),
        faces=np.asarray(compact_faces, dtype=np.uint32),
        station_node_ids=np.asarray(station_node_ids, dtype=np.uint32),
        station_xz=np.asarray(station_xz, dtype=np.float32),
        sea_corners_xz=np.asarray(
            [
                [min_x - origin_x, min_z - origin_z],
                [max_x - origin_x, min_z - origin_z],
                [max_x - origin_x, max_z - origin_z],
                [min_x - origin_x, max_z - origin_z],
            ],
            dtype=np.float32,
        ),
        district_lines_xz=_project_district_lines(
            districts, projection, origin_x, origin_z
        ),
        horizontal_span_m=float(horizontal_span),
    )
    return PreparedGeometry(domain=domain, frames=frames)
