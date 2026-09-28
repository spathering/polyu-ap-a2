"""Domain models shared across data, geometry, rendering and web export."""

from dataclasses import dataclass
from datetime import date

import numpy as np


@dataclass(frozen=True)
class WeatherDataset:
    """Validated daily values arranged as date-by-station arrays."""

    dates: tuple[date, ...]
    station_codes: tuple[str, ...]
    station_names: tuple[str, ...]
    latitudes: np.ndarray
    longitudes: np.ndarray
    elevations_m: np.ndarray
    temperatures_c: np.ndarray
    rainfall_mm: np.ndarray
    rainfall_trace: np.ndarray


@dataclass(frozen=True)
class TerrainData:
    """A source raster used only to classify land and sea."""

    longitudes: np.ndarray
    latitudes: np.ndarray
    elevations_m: np.ndarray


@dataclass(frozen=True)
class DistrictBoundary:
    """One official district geometry and its bilingual labels."""

    code: str
    name_en: str
    name_zh: str
    geometry: object


@dataclass(frozen=True)
class MapDomain:
    """Static X-Z topology shared by the base and both weather surfaces."""

    nodes_xz: np.ndarray
    faces: np.ndarray
    station_node_ids: np.ndarray
    station_xz: np.ndarray
    sea_corners_xz: np.ndarray
    district_lines_xz: tuple[np.ndarray, ...]
    horizontal_span_m: float


@dataclass(frozen=True)
class FieldFrames:
    """Precomputed source-unit fields and their fixed visual Y mappings."""

    temperature_c: np.ndarray
    rainfall_mm: np.ndarray
    temperature_y: np.ndarray
    rainfall_y: np.ndarray


@dataclass(frozen=True)
class PreparedGeometry:
    """Complete immutable geometry and field state for all render targets."""

    domain: MapDomain
    frames: FieldFrames
