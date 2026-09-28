"""Load committed Hong Kong and official district boundary sources."""

import json

from shapely import union_all
from shapely.geometry import shape

from hk_weather.core.models import DistrictBoundary
from hk_weather.core.paths import BOUNDARY, DISTRICT_BOUNDARY


def load_hong_kong_boundary(path=BOUNDARY):
    """Select the Hong Kong feature and return a valid Shapely geometry."""
    if not path.is_file():
        raise FileNotFoundError(
            f"missing boundary source: {path}; run `uv run fetch.py` once"
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    features = document.get("features", [])
    for feature in features:
        searchable = " ".join(str(value) for value in feature.get("properties", {}).values())
        if "hong kong" not in searchable.lower():
            continue
        boundary = shape(feature["geometry"])
        if not boundary.is_valid:
            boundary = boundary.buffer(0)
        if boundary.is_empty:
            raise RuntimeError("Hong Kong boundary geometry is empty")
        return boundary

    names = [feature.get("properties", {}).get("shapeName", "?") for feature in features]
    raise RuntimeError(f"Hong Kong not found in boundary file; available names: {names}")


def load_district_boundaries(path=DISTRICT_BOUNDARY):
    """Return all 18 official district geometries in WGS84 coordinates."""
    if not path.is_file():
        raise FileNotFoundError(
            f"missing district boundary source: {path}; run `uv run fetch.py` once"
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    districts = []
    for feature in document.get("features", []):
        properties = feature.get("properties", {})
        geometry = shape(feature["geometry"])
        if not geometry.is_valid:
            geometry = geometry.buffer(0)
        districts.append(
            DistrictBoundary(
                code=str(properties.get("地區號碼", "")),
                name_en=str(properties.get("District", "")),
                name_zh=str(properties.get("地區", "")),
                geometry=geometry,
            )
        )
    if len(districts) != 18 or any(item.geometry.is_empty for item in districts):
        raise RuntimeError(f"expected 18 non-empty districts, found {len(districts)}")
    return tuple(districts)


def district_union(districts):
    """Return one valid territory geometry for clipping the binary land mask."""
    value = union_all([district.geometry for district in districts])
    if not value.is_valid:
        value = value.buffer(0)
    if value.is_empty:
        raise RuntimeError("district boundary union is empty")
    return value
