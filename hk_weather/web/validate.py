"""Validate the built static site and its versioned payload."""

import hashlib
import json

import numpy as np

from hk_weather.core.config import WEB_ARTIFACT_TARGET_BYTES, WEB_SCHEMA_VERSION
from hk_weather.core.paths import SITE
from hk_weather.geometry.height_mapping import rainfall_to_y, temperature_to_y


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_site(site=SITE):
    index = site / "index.html"
    manifest_path = site / "data" / "manifest.json"
    if not index.is_file() or not manifest_path.is_file():
        raise RuntimeError("site build is missing index.html or data/manifest.json")
    html = index.read_text(encoding="utf-8")
    if 'src="/' in html or 'href="/' in html:
        raise RuntimeError("site contains root-relative asset URLs")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["schemaVersion"] != WEB_SCHEMA_VERSION:
        raise RuntimeError("unexpected web schema version")
    if len(manifest["dates"]) != 30 or manifest["stationCount"] != 21:
        raise RuntimeError("web manifest does not contain 30 dates and 21 stations")

    records = [manifest["topology"], *manifest["files"].values()]
    for record in records:
        path = site / "data" / record["path"]
        if not path.is_file() or path.stat().st_size != record["bytes"]:
            raise RuntimeError(f"web payload size mismatch: {record['path']}")
        if _sha256(path) != record["sha256"]:
            raise RuntimeError(f"web payload checksum mismatch: {record['path']}")

    node_count = manifest["nodeCount"]
    date_count = len(manifest["dates"])
    for key in ("temperature-y.f32", "temperature-values.f32", "rainfall-y.f32", "rainfall-values.f32"):
        record = manifest["files"][key]
        if record["shape"] != [date_count, node_count]:
            raise RuntimeError(f"unexpected frame shape for {key}: {record['shape']}")

    temperature_y = np.fromfile(site / "data" / "temperature-y.f32", dtype="<f4")
    rainfall_y = np.fromfile(site / "data" / "rainfall-y.f32", dtype="<f4")
    temperature_values = np.fromfile(
        site / "data" / "temperature-values.f32", dtype="<f4"
    )
    rainfall_values = np.fromfile(
        site / "data" / "rainfall-values.f32", dtype="<f4"
    )
    if not np.all(temperature_y <= 1e-7) or not np.all(rainfall_y >= -1e-7):
        raise RuntimeError("web surface Y signs are invalid")
    horizontal_span = manifest["horizontalSpan"]
    if not np.allclose(
        temperature_y,
        temperature_to_y(temperature_values, horizontal_span),
        atol=2e-3,
    ):
        raise RuntimeError("web temperature height direction is invalid")
    if not np.allclose(
        rainfall_y,
        rainfall_to_y(rainfall_values, horizontal_span),
        atol=2e-3,
    ):
        raise RuntimeError("web rainfall height direction is invalid")
    if manifest["temperature"]["baseline"] != 14.0:
        raise RuntimeError("temperature baseline is not 14 °C")
    if manifest["rainfall"]["baseline"] != 0.0:
        raise RuntimeError("rainfall baseline is not 0 mm")
    if manifest["camera"]["pitchRange"] != [-60.0, 60.0]:
        raise RuntimeError("web camera pitch range is not -60–60 degrees")
    grid = manifest.get("grid", {})
    if grid.get("divisions") != 24 or grid.get("majorEvery") != 4:
        raise RuntimeError("web manifest has no valid two-scale reference grid")
    if not manifest.get("depthFog"):
        raise RuntimeError("web manifest has no screen-space depth fog settings")

    total_bytes = sum(path.stat().st_size for path in site.rglob("*") if path.is_file())
    if total_bytes > WEB_ARTIFACT_TARGET_BYTES:
        raise RuntimeError(
            f"site is {total_bytes / 1024 / 1024:.1f} MB; target is "
            f"{WEB_ARTIFACT_TARGET_BYTES / 1024 / 1024:.0f} MB"
        )
    print(f"validated site: {total_bytes / 1024 / 1024:.1f} MB")
    return manifest
