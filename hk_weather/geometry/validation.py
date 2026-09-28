"""Leave-one-station-out scoring for interpolation profiles."""

import numpy as np

from hk_weather.geometry.interpolation import interpolate_fields, inverse_distance_weights


def leave_one_station_out(station_xz, values, *, power, neighbours, transform):
    """Return prediction and error arrays for every date/station observation."""
    station_xz = np.asarray(station_xz, dtype=float)
    values = np.asarray(values, dtype=float)
    predictions = np.empty_like(values)
    for held_index in range(len(station_xz)):
        keep = np.arange(len(station_xz)) != held_index
        weights = inverse_distance_weights(
            station_xz[[held_index]],
            station_xz[keep],
            power=power,
            neighbours=min(neighbours, int(np.sum(keep))),
        )
        predictions[:, held_index] = interpolate_fields(
            weights, values[:, keep], transform=transform
        )[:, 0]
    return predictions, predictions - values


def error_metrics(values, errors, *, wet_only=False):
    mask = np.asarray(values) > 0.0 if wet_only else np.ones_like(values, dtype=bool)
    selected = np.asarray(errors)[mask]
    if not len(selected):
        return {"count": 0, "mae": None, "rmse": None, "max_abs": None}
    return {
        "count": int(len(selected)),
        "mae": float(np.mean(np.abs(selected))),
        "rmse": float(np.sqrt(np.mean(np.square(selected)))),
        "max_abs": float(np.max(np.abs(selected))),
    }
