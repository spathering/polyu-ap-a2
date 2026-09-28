"""Canonical project paths shared by all package layers."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA = PROJECT_ROOT / "data"
RAW = DATA / "raw"
DERIVED = DATA / "derived"
TEMPERATURE = RAW / "temperature"
RAINFALL = RAW / "rainfall"
STATION_PAGE = RAW / "hko-weather-stations.html"
OUT = PROJECT_ROOT / "out"
WEATHER_DATA = DATA / "hk-weather-2026-04.csv"
BOUNDARY_METADATA = RAW / "geoboundaries-china-adm1-metadata.json"
BOUNDARY = RAW / "geoboundaries-china-adm1.geojson"
MAP = RAW / "map"
DISTRICT_BOUNDARY = MAP / "hksar-18-district-boundary.json"
TERRAIN = RAW / "terrain"
INTERPOLATION_REPORT = DERIVED / "interpolation-report.json"
WEB_ROOT = PROJECT_ROOT / "web"
WEB_DATA_STAGING = WEB_ROOT / "public" / "data"
SITE = PROJECT_ROOT / "site"
