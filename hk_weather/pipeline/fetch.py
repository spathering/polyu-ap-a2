"""Fetch HKO raw source files once and preserve their response bytes."""

import requests

from hk_weather.core.config import SOURCE_STATIONS, YEAR
from hk_weather.core.paths import PROJECT_ROOT, RAINFALL, RAW, STATION_PAGE, TEMPERATURE


TEMPERATURE_URL = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
RAINFALL_URL = (
    "https://data.weather.gov.hk/weatherAPI/cis/csvfile/"
    "{station}/{year}/daily_{station}_RF_{year}.csv"
)
STATION_URL = "https://www.weather.gov.hk/en/cis/stn.htm"
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

    print(f"\n{len(SOURCE_STATIONS)} candidate station pairs fetched once. "
          "Now run: uv run audit.py --months")
