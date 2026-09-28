"""The only coordinate-conversion implementation used by the project."""

import numpy as np
from pyproj import Transformer
from shapely.ops import transform

from hk_weather.core.config import MAP_CRS


class MapProjection:
    """Project WGS84 longitude/latitude coordinates into a shared metre grid."""

    def __init__(self, target_crs=MAP_CRS):
        self.forward = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)

    def points(self, longitudes, latitudes):
        x, y = self.forward.transform(longitudes, latitudes)
        return np.asarray(x, dtype=float), np.asarray(y, dtype=float)

    def geometry(self, value):
        return transform(self.forward.transform, value)
