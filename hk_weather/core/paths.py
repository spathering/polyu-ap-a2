"""Canonical project paths shared by all package layers."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA = PROJECT_ROOT / "data"
RAW = DATA / "raw"
TEMPERATURE = RAW / "temperature"
RAINFALL = RAW / "rainfall"
STATION_PAGE = RAW / "hko-weather-stations.html"
OUT = PROJECT_ROOT / "out"
