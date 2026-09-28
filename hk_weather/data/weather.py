"""Read the tidy weather CSV into one validated domain model."""

import csv
from datetime import date

import numpy as np

from hk_weather.core.config import STATIONS
from hk_weather.core.models import WeatherDataset
from hk_weather.core.paths import WEATHER_DATA


def load_weather(path=WEATHER_DATA):
    """Load exactly one value for every April date and selected station."""
    if not path.is_file():
        raise FileNotFoundError(f"missing prepared weather data: {path}")

    records = {}
    metadata = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            day = date.fromisoformat(row["date"])
            code = row["station"]
            key = (day, code)
            if key in records:
                raise RuntimeError(f"duplicate weather row: {day} {code}")
            if row["rainfall_trace"] not in {"true", "false"}:
                raise RuntimeError(f"invalid rainfall_trace value in {key}")
            records[key] = (
                float(row["mean_temperature_c"]),
                float(row["total_rainfall_mm"]),
                row["rainfall_trace"] == "true",
            )
            current = (
                row["station_name"],
                float(row["latitude"]),
                float(row["longitude"]),
                float(row["elevation_m"]),
            )
            if code in metadata and metadata[code] != current:
                raise RuntimeError(f"station metadata changes between rows: {code}")
            metadata[code] = current

    dates = tuple(sorted({key[0] for key in records}))
    station_codes = tuple(STATIONS)
    expected = {(day, code) for day in dates for code in station_codes}
    if set(records) != expected or len(dates) != 30:
        missing = sorted(expected - set(records))
        extra = sorted(set(records) - expected)
        raise RuntimeError(
            f"weather grid is incomplete: {len(dates)} dates, "
            f"missing={missing[:3]}, extra={extra[:3]}"
        )

    temperatures = np.empty((len(dates), len(station_codes)), dtype=float)
    rainfall = np.empty_like(temperatures)
    traces = np.empty_like(temperatures, dtype=bool)
    for day_index, day in enumerate(dates):
        for station_index, code in enumerate(station_codes):
            temperatures[day_index, station_index], rainfall[day_index, station_index], traces[
                day_index, station_index
            ] = records[(day, code)]

    return WeatherDataset(
        dates=dates,
        station_codes=station_codes,
        station_names=tuple(metadata[code][0] for code in station_codes),
        latitudes=np.array([metadata[code][1] for code in station_codes]),
        longitudes=np.array([metadata[code][2] for code in station_codes]),
        elevations_m=np.array([metadata[code][3] for code in station_codes]),
        temperatures_c=temperatures,
        rainfall_mm=rainfall,
        rainfall_trace=traces,
    )
