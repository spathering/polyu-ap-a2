"""Fixed reversible mappings between source units and the Y display axis."""

import numpy as np

from hk_weather.core.config import (
    RAINFALL_BASELINE_MM,
    RAINFALL_HEIGHT_FRACTION,
    RAINFALL_RANGE_MM,
    TEMPERATURE_BASELINE_C,
    TEMPERATURE_HEIGHT_FRACTION,
    TEMPERATURE_RANGE_C,
)


def temperature_to_y(values_c, horizontal_span_m):
    _, high = TEMPERATURE_RANGE_C
    normalised = np.clip(
        (np.asarray(values_c) - TEMPERATURE_BASELINE_C)
        / (high - TEMPERATURE_BASELINE_C),
        0.0,
        1.0,
    )
    return -horizontal_span_m * TEMPERATURE_HEIGHT_FRACTION * normalised


def rainfall_to_y(values_mm, horizontal_span_m):
    _, high = RAINFALL_RANGE_MM
    normalised = np.clip(
        (np.asarray(values_mm) - RAINFALL_BASELINE_MM)
        / (high - RAINFALL_BASELINE_MM),
        0.0,
        1.0,
    )
    return horizontal_span_m * RAINFALL_HEIGHT_FRACTION * normalised


def y_to_temperature(values_y, horizontal_span_m):
    normalised = -np.asarray(values_y) / (
        horizontal_span_m * TEMPERATURE_HEIGHT_FRACTION
    )
    _, high = TEMPERATURE_RANGE_C
    return TEMPERATURE_BASELINE_C + normalised * (
        high - TEMPERATURE_BASELINE_C
    )


def y_to_rainfall(values_y, horizontal_span_m):
    normalised = np.asarray(values_y) / (
        horizontal_span_m * RAINFALL_HEIGHT_FRACTION
    )
    _, high = RAINFALL_RANGE_MM
    return RAINFALL_BASELINE_MM + normalised * (
        high - RAINFALL_BASELINE_MM
    )
