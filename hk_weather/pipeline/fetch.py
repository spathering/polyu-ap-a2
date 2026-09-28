"""Fetch every raw source once and preserve its response bytes."""

import json
import math

import requests

from hk_weather.core.config import MAP_BOUNDS, SOURCE_STATIONS, TERRAIN_ZOOM, YEAR
from hk_weather.core.paths import (
    BOUNDARY,
    BOUNDARY_METADATA,
    DISTRICT_BOUNDARY,
    PROJECT_ROOT,
    RAINFALL,
    RAW,
    STATION_PAGE,
    TEMPERATURE,
    TERRAIN,
)


TEMPERATURE_URL = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
RAINFALL_URL = (
    "https://data.weather.gov.hk/weatherAPI/cis/csvfile/"
    "{station}/{year}/daily_{station}_RF_{year}.csv"
)
STATION_URL = "https://www.weather.gov.hk/en/cis/stn.htm"
BOUNDARY_METADATA_URL = "https://www.geoboundaries.org/api/current/gbOpen/CHN/ADM1/"
DISTRICT_BOUNDARY_URL = (
    "https://www.had.gov.hk/psi/hong-kong-administrative-boundaries/"
    "hksar_18_district_boundary.json"
)
TERRAIN_URL = (
    "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
)
HEADERS = {"User-Agent": "SD5913 PolyU assignment 2 data visualisation"}


def fetch_once(session, url, path, params=None):
    """Save one raw HTTP response unless it is already present."""
    if path.is_file():
        print(f"keep  {path.relative_to(PROJECT_ROOT)} ({path.stat().st_size} bytes)")
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    response = session.get(url, params=params, timeout=60, headers=HEADERS)
    response.raise_for_status()
    path.write_bytes(response.content)
    print(f"saved {path.relative_to(PROJECT_ROOT)} ({path.stat().st_size} bytes)")
    return path


def tile_number(longitude, latitude, zoom):
    """Return the XYZ tile containing one longitude/latitude coordinate."""
    scale = 2 ** zoom
    x = int((longitude + 180.0) / 360.0 * scale)
    latitude_radians = math.radians(latitude)
    y = int(
        (1.0 - math.asinh(math.tan(latitude_radians)) / math.pi)
        / 2.0
        * scale
    )
    return x, y


def fetch_map_sources(session):
    """Cache a Hong Kong boundary source and the small covering terrain tile set."""
    fetch_once(session, DISTRICT_BOUNDARY_URL, DISTRICT_BOUNDARY)
    fetch_once(session, BOUNDARY_METADATA_URL, BOUNDARY_METADATA)
    metadata = json.loads(BOUNDARY_METADATA.read_text(encoding="utf-8"))
    boundary_url = metadata.get("gjDownloadURL")
    if not boundary_url:
        raise RuntimeError("geoBoundaries metadata has no gjDownloadURL")
    fetch_once(session, boundary_url, BOUNDARY)

    west, south, east, north = MAP_BOUNDS
    west_x, north_y = tile_number(west, north, TERRAIN_ZOOM)
    east_x, south_y = tile_number(east, south, TERRAIN_ZOOM)
    for tile_x in range(west_x, east_x + 1):
        for tile_y in range(north_y, south_y + 1):
            path = TERRAIN / f"terrarium-z{TERRAIN_ZOOM}-x{tile_x}-y{tile_y}.png"
            fetch_once(
                session,
                TERRAIN_URL.format(z=TERRAIN_ZOOM, x=tile_x, y=tile_y),
                path,
            )


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        fetch_once(session, STATION_URL, STATION_PAGE)

        for station, name in SOURCE_STATIONS.items():
            print(f"\n{station} — {name}")
            fetch_once(
                session,
                TEMPERATURE_URL,
                TEMPERATURE / f"daily-mean-temperature-{station}-{YEAR}.csv",
                params={
                    "dataType": "CLMTEMP",
                    "station": station,
                    "year": YEAR,
                    "rformat": "csv",
                },
            )
            fetch_once(
                session,
                RAINFALL_URL.format(station=station, year=YEAR),
                RAINFALL / f"daily-total-rainfall-{station}-{YEAR}.csv",
            )

        print("\nmap sources")
        fetch_map_sources(session)

    print(f"\n{len(SOURCE_STATIONS)} candidate station pairs and local map sources "
          "are cached. Now run: uv run audit.py --months")
