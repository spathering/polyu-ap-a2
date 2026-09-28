"""Export prepared Python domain data for the static VTK.js viewer."""

import json

import numpy as np

from hk_weather.core.config import (
    AUTOPLAY_INTERVAL_S,
    AUTOPLAY_RESUME_DELAY_S,
    CAMERA_DISTANCE_FACTOR,
    CAMERA_PITCH_RANGE_DEG,
    INITIAL_CAMERA_PITCH_DEG,
    LAND_COLOUR,
    LAND_OPACITY,
    RAINFALL_COLOURS,
    RAINFALL_OPACITY,
    RAINFALL_RANGE_MM,
    SCREENSHOT_DAY_INDEX,
    SEA_COLOUR,
    SEA_OPACITY,
    TEMPERATURE_COLOURS,
    TEMPERATURE_OPACITY,
    TEMPERATURE_RANGE_C,
    WEB_SCHEMA_VERSION,
)
from hk_weather.core.paths import WEB_DATA_STAGING
from hk_weather.web.schema import file_record


def _write_array(path, values, dtype):
    array = np.asarray(values, dtype=dtype)
    path.write_bytes(array.tobytes(order="C"))
    return array


def export_web_data(weather, prepared, directory=WEB_DATA_STAGING):
    """Write one topology and precomputed frame arrays with integrity metadata."""
    directory.mkdir(parents=True, exist_ok=True)
    domain = prepared.domain
    frames = prepared.frames

    topology_path = directory / "topology.bin"
    nodes = np.asarray(domain.nodes_xz, dtype="<f4")
    faces = np.asarray(domain.faces, dtype="<u4")
    topology_path.write_bytes(nodes.tobytes(order="C") + faces.tobytes(order="C"))
    topology = {
        "path": topology_path.relative_to(directory).as_posix(),
        "bytes": topology_path.stat().st_size,
        "nodes": {
            "dtype": "<f4",
            "shape": list(nodes.shape),
            "offset": 0,
            "bytes": int(nodes.nbytes),
        },
        "faces": {
            "dtype": "<u4",
            "shape": list(faces.shape),
            "offset": int(nodes.nbytes),
            "bytes": int(faces.nbytes),
        },
    }
    topology.update(file_record(topology_path, directory))

    array_specs = (
        ("temperature-y.f32", frames.temperature_y, "<f4"),
        ("temperature-values.f32", frames.temperature_c, "<f4"),
        ("rainfall-y.f32", frames.rainfall_y, "<f4"),
        ("rainfall-values.f32", frames.rainfall_mm, "<f4"),
    )
    files = {}
    for name, values, dtype in array_specs:
        path = directory / name
        array = _write_array(path, values, dtype)
        files[name] = file_record(
            path, directory, dtype=dtype, shape=array.shape, offset=0
        )

    districts_path = directory / "district-lines.json"
    districts_path.write_text(
        json.dumps(
            [[[round(float(x), 2), round(float(z), 2)] for x, z in line]
             for line in domain.district_lines_xz],
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    files[districts_path.name] = file_record(districts_path, directory)

    stations_path = directory / "stations.json"
    stations = []
    for index, code in enumerate(weather.station_codes):
        stations.append(
            {
                "code": code,
                "name": weather.station_names[index],
                "x": round(float(domain.station_xz[index, 0]), 3),
                "z": round(float(domain.station_xz[index, 1]), 3),
                "node": int(domain.station_node_ids[index]),
                "temperature": weather.temperatures_c[:, index].tolist(),
                "rainfall": weather.rainfall_mm[:, index].tolist(),
                "trace": weather.rainfall_trace[:, index].tolist(),
            }
        )
    stations_path.write_text(
        json.dumps(stations, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    files[stations_path.name] = file_record(stations_path, directory)

    manifest = {
        "schemaVersion": WEB_SCHEMA_VERSION,
        "title": "Hong Kong Weather Surfaces",
        "dates": [value.isoformat() for value in weather.dates],
        "defaultDayIndex": SCREENSHOT_DAY_INDEX,
        "nodeCount": int(len(domain.nodes_xz)),
        "faceCount": int(len(domain.faces)),
        "stationCount": int(len(weather.station_codes)),
        "horizontalSpan": domain.horizontal_span_m,
        "seaCorners": domain.sea_corners_xz.tolist(),
        "topology": topology,
        "files": files,
        "temperature": {
            "range": list(TEMPERATURE_RANGE_C),
            "colours": TEMPERATURE_COLOURS,
            "yFile": "temperature-y.f32",
            "valueFile": "temperature-values.f32",
        },
        "rainfall": {
            "range": list(RAINFALL_RANGE_MM),
            "colours": RAINFALL_COLOURS,
            "yFile": "rainfall-y.f32",
            "valueFile": "rainfall-values.f32",
        },
        "base": {
            "landColour": LAND_COLOUR,
            "landOpacity": LAND_OPACITY,
            "seaColour": SEA_COLOUR,
            "seaOpacity": SEA_OPACITY,
            "districtFile": districts_path.name,
        },
        "stationsFile": stations_path.name,
        "camera": {
            "pitchRange": list(CAMERA_PITCH_RANGE_DEG),
            "initialPitch": INITIAL_CAMERA_PITCH_DEG,
            "distanceFactor": CAMERA_DISTANCE_FACTOR,
        },
        "surfaceOpacity": {
            "temperature": TEMPERATURE_OPACITY,
            "rainfall": RAINFALL_OPACITY,
        },
        "timeline": {
            "intervalMs": round(AUTOPLAY_INTERVAL_S * 1000),
            "resumeDelayMs": round(AUTOPLAY_RESUME_DELAY_S * 1000),
        },
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote web payload: {directory} ({len(domain.nodes_xz)} nodes)")
    return manifest_path
