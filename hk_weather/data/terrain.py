"""Decode committed Terrarium tiles for binary land/sea classification only."""

import math

import numpy as np
from PIL import Image

from hk_weather.core.config import MAP_BOUNDS, TERRAIN_DOWNSAMPLE, TERRAIN_ZOOM
from hk_weather.core.models import TerrainData
from hk_weather.core.paths import TERRAIN


TILE_SIZE = 256


def tile_number(longitude, latitude, zoom):
    scale = 2 ** zoom
    x = int((longitude + 180.0) / 360.0 * scale)
    latitude_radians = math.radians(latitude)
    y = int((1.0 - math.asinh(math.tan(latitude_radians)) / math.pi) / 2.0 * scale)
    return x, y


def decode_tile(path):
    """Decode Mapzen's R*256 + G + B/256 - 32768 Terrarium formula."""
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    if rgb.shape != (TILE_SIZE, TILE_SIZE, 3):
        raise RuntimeError(f"unexpected terrain tile shape in {path}: {rgb.shape}")
    return rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768.0


def load_terrain(
    directory=TERRAIN,
    bounds=MAP_BOUNDS,
    zoom=TERRAIN_ZOOM,
    downsample=TERRAIN_DOWNSAMPLE,
):
    """Mosaic, crop and downsample source values without rendering elevation."""
    west, south, east, north = bounds
    west_x, north_y = tile_number(west, north, zoom)
    east_x, south_y = tile_number(east, south, zoom)
    tile_xs = list(range(west_x, east_x + 1))
    tile_ys = list(range(north_y, south_y + 1))

    rows = []
    for tile_y in tile_ys:
        row = []
        for tile_x in tile_xs:
            path = directory / f"terrarium-z{zoom}-x{tile_x}-y{tile_y}.png"
            if not path.is_file():
                raise FileNotFoundError(
                    f"missing terrain tile: {path}; run `uv run fetch.py` once"
                )
            row.append(decode_tile(path))
        rows.append(np.concatenate(row, axis=1))
    elevations = np.concatenate(rows, axis=0)

    pixel_x = np.arange(elevations.shape[1]) + tile_xs[0] * TILE_SIZE + 0.5
    pixel_y = np.arange(elevations.shape[0]) + tile_ys[0] * TILE_SIZE + 0.5
    world_pixels = TILE_SIZE * (2 ** zoom)
    longitudes = pixel_x / world_pixels * 360.0 - 180.0
    mercator_y = math.pi * (1.0 - 2.0 * pixel_y / world_pixels)
    latitudes = np.degrees(np.arctan(np.sinh(mercator_y)))

    column_indices = np.flatnonzero((longitudes >= west) & (longitudes <= east))
    row_indices = np.flatnonzero((latitudes >= south) & (latitudes <= north))
    if not len(column_indices) or not len(row_indices):
        raise RuntimeError("terrain crop does not overlap the configured map bounds")
    column_indices = column_indices[::downsample]
    row_indices = row_indices[::downsample]
    return TerrainData(
        longitudes=longitudes[column_indices],
        latitudes=latitudes[row_indices],
        elevations_m=elevations[np.ix_(row_indices, column_indices)],
    )
