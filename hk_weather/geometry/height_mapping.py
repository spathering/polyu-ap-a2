"""Fixed reversible mappings between source units and the Y display axis."""

import numpy as np

from hk_weather.core.config import (
    RAINFALL_HEIGHT_FRACTION,
    RAINFALL_RANGE_MM,
    TEMPERATURE_GAP_FRACTION,
    TEMPERATURE_HEIGHT_FRACTION,
    TEMPERATURE_RANGE_C,
)


def temperature_to_y(values_c, horizontal_span_m):
    low, high = TEMPERATURE_RANGE_C
    normalised = np.clip((np.asarray(values_c) - low) / (high - low), 0.0, 1.0)
    return horizontal_span_m * (
        TEMPERATURE_GAP_FRACTION + TEMPERATURE_HEIGHT_FRACTION * normalised
    )


def rainfall_to_y(values_mm, horizontal_span_m):
    low, high = RAINFALL_RANGE_MM
    normalised = np.clip((np.asarray(values_mm) - low) / (high - low), 0.0, 1.0)
    return -horizontal_span_m * RAINFALL_HEIGHT_FRACTION * normalised


def y_to_temperature(values_y, horizontal_span_m):
    normalised = (
        np.asarray(values_y) / horizontal_span_m - TEMPERATURE_GAP_FRACTION
    ) / TEMPERATURE_HEIGHT_FRACTION
    low, high = TEMPERATURE_RANGE_C
    return low + normalised * (high - low)


def y_to_rainfall(values_y, horizontal_span_m):
    normalised = -np.asarray(values_y) / (
        horizontal_span_m * RAINFALL_HEIGHT_FRACTION
    )
    low, high = RAINFALL_RANGE_MM
    return low + normalised * (high - low)
