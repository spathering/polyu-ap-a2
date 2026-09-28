"""Evaluate and record fixed interpolation profiles."""

import json

import numpy as np

from hk_weather.core.paths import INTERPOLATION_REPORT
from hk_weather.data.weather import load_weather
from hk_weather.geometry.projection import MapProjection
from hk_weather.geometry.validation import error_metrics, leave_one_station_out


POWERS = (1.5, 2.0, 2.5, 3.0)
NEIGHBOURS = (8, 12, 16, 20)


def _profiles(station_xz, values, transform, rainfall=False):
    reports = []
    for power in POWERS:
        for neighbours in NEIGHBOURS:
            predictions, errors = leave_one_station_out(
                station_xz,
                values,
                power=power,
                neighbours=neighbours,
                transform=transform,
            )
            report = {
                "power": power,
                "neighbours": neighbours,
                "all": error_metrics(values, errors),
            }
            if rainfall:
                report["wet"] = error_metrics(values, errors, wet_only=True)
                report["rank_score"] = report["all"]["mae"] + report["wet"]["mae"]
            else:
                report["rank_score"] = report["all"]["rmse"]
            reports.append(report)
    reports.sort(key=lambda item: (item["rank_score"], item["power"], -item["neighbours"]))
    return reports


def main():
    weather = load_weather()
    projection = MapProjection()
    station_x, station_z = projection.points(weather.longitudes, weather.latitudes)
    station_xz = np.column_stack((station_x, station_z))
    temperature = _profiles(
        station_xz, weather.temperatures_c, transform="identity", rainfall=False
    )
    rainfall = _profiles(
        station_xz, weather.rainfall_mm, transform="log1p", rainfall=True
    )
    report = {
        "method": "leave-one-station-out across 30 dates and 21 stations",
        "temperature": {"selected": temperature[0], "candidates": temperature},
        "rainfall": {"selected": rainfall[0], "candidates": rainfall},
    }
    INTERPOLATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    INTERPOLATION_REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {INTERPOLATION_REPORT.relative_to(INTERPOLATION_REPORT.parents[2])}")
    print("temperature", temperature[0])
    print("rainfall", rainfall[0])
    return report
