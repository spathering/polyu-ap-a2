"""Exact k-nearest inverse-distance interpolation for both weather fields."""

import numpy as np

from hk_weather.core.config import INTERPOLATION_EXACT_TOLERANCE_M


def inverse_distance_weights(
    target_xz,
    station_xz,
    *,
    power,
    neighbours,
    exact_tolerance_m=INTERPOLATION_EXACT_TOLERANCE_M,
):
    """Return non-negative normalised weights, preserving exact station hits."""
    target_xz = np.asarray(target_xz, dtype=float)
    station_xz = np.asarray(station_xz, dtype=float)
    if target_xz.ndim != 2 or target_xz.shape[1] != 2:
        raise ValueError("target_xz must have shape [target, 2]")
    if station_xz.ndim != 2 or station_xz.shape[1] != 2:
        raise ValueError("station_xz must have shape [station, 2]")
    if power <= 0:
        raise ValueError("IDW power must be positive")

    station_count = station_xz.shape[0]
    neighbour_count = min(max(int(neighbours), 1), station_count)
    offsets = target_xz[:, None, :] - station_xz[None, :, :]
    distances = np.linalg.norm(offsets, axis=2)
    weights = np.zeros_like(distances)

    exact_rows, exact_columns = np.where(distances <= exact_tolerance_m)
    first_exact = {}
    for row, column in zip(exact_rows.tolist(), exact_columns.tolist()):
        first_exact.setdefault(row, column)

    regular_rows = np.array(
        [row for row in range(len(target_xz)) if row not in first_exact], dtype=int
    )
    if len(regular_rows):
        row_distances = distances[regular_rows]
        nearest = np.argpartition(
            row_distances, neighbour_count - 1, axis=1
        )[:, :neighbour_count]
        selected_distances = np.take_along_axis(row_distances, nearest, axis=1)
        selected_weights = 1.0 / np.power(selected_distances, power)
        selected_weights /= selected_weights.sum(axis=1, keepdims=True)
        for local_row, global_row in enumerate(regular_rows):
            weights[global_row, nearest[local_row]] = selected_weights[local_row]

    for row, column in first_exact.items():
        weights[row, column] = 1.0

    if not np.all(np.isfinite(weights)) or np.any(weights < 0):
        raise RuntimeError("IDW produced invalid weights")
    if not np.allclose(weights.sum(axis=1), 1.0, atol=1e-10):
        raise RuntimeError("IDW weights do not sum to one")
    return weights


def interpolate_fields(weights, values, *, transform="identity"):
    """Interpolate date-by-station values into date-by-target fields."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or values.shape[1] != weights.shape[1]:
        raise ValueError("values must have shape [date, station]")
    if transform == "identity":
        transformed = values
        restore = lambda result: result
    elif transform == "log1p":
        if np.any(values < 0):
            raise ValueError("log1p interpolation cannot accept negative values")
        transformed = np.log1p(values)
        restore = lambda result: np.maximum(np.expm1(result), 0.0)
    else:
        raise ValueError(f"unknown interpolation transform: {transform}")
    return restore(transformed @ weights.T)
