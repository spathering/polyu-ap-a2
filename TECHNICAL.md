# Technical Plan

## Python stack

The application will be implemented in Python with NumPy, PyVista and VTK. Shapely clips geometry to the Hong Kong boundary, PyProj supplies one shared metric projection, and Pillow decodes locally cached terrain PNG tiles. PyVista supplies the 3D mesh, camera, lighting, slider widget, timers, picking, text actors and off-screen screenshot.

The planned `plot.py` dependency block is:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=2,<3",
#   "Pillow>=11,<13",
#   "pyproj>=3.7,<4",
#   "pyvista>=0.49,<0.50",
#   "shapely>=2,<3",
#   "vtk>=9.5,<10",
# ]
# ///
```

Plotly, Dash, Matplotlib, Kaleido and online map tiles are not part of the implementation. `uv run plot.py` will use local data, write `out/hong-kong-weather-april.png`, then open the interactive 3D window. Root scripts remain small PEP 723 entry points; all implementation code belongs in the `hk_weather/` package.

Current transition status: the fetch, audit and preparation logic already lives in `hk_weather/core/` and `hk_weather/pipeline/`, and their root files are thin entry points. The untouched Matplotlib template has temporarily moved to `hk_weather/app.py`; it will be replaced, together with its temporary dependency block, by the PyVista implementation described above.

## Package layers

```text
hk_weather/
├── app.py
├── core/          config, dataclasses, interfaces, timeline state
├── pipeline/      fetch, audit and preparation implementations
├── data/          weather, boundary and terrain readers; validation
├── geometry/      projection, terrain mesh, IDW and rain geometry
├── render/        scene, terrain, rain, station, legends and camera
├── interaction/   frame controller, timeline, cursor probe, highlight,
│                  and camera guard
└── output/        screenshot generation
```

Root `fetch.py`, `audit.py`, `prepare_data.py` and `plot.py` only import and call package entry functions. `app.py` is the only composition layer allowed to know every subsystem.

Dependencies flow in one direction: `core` is independent; `data` produces domain models; `geometry` consumes models and returns arrays or meshes; `render` consumes geometry and returns scene handles; `interaction` updates those handles; `output` uses the same scene builder as the interactive app. Data modules never know about actors, render modules never read CSV files, and interaction modules never repeat interpolation or projection.

Shared foundations have one implementation each:

- `core/config.py`: paths, colour scales, timing and camera limits.
- `geometry/projection.py`: every coordinate conversion.
- `geometry/interpolation.py`: IDW for both interactive and still output.
- `interaction/frame_controller.py`: the only function that applies a date.
- `render/scene.py`: the only scene factory for window and screenshot.
- `interaction/cursor_probe.py`: map picking and nearest-station calculation.

Both the autoplay timer and slider callback call `FrameController.apply(day_index)`, preventing separate update paths for temperature, rainfall and text.

## Interaction implementation

PyVista's slider widget is the only visible control. It snaps values `0..29` to dates and fires continuously while dragged. A timer advances the same date state every 900 ms. Dragging temporarily suppresses timer changes; playback resumes about two seconds after release.

A `MouseMoveEvent` observer is throttled to about 30 Hz. A cell picker converts the cursor to a position on the terrain. NumPy finds the nearest of 21 projected station positions. One reusable screen-space text actor follows the cursor, while one reusable halo actor moves to the selected station and the selected rainfall actor changes appearance. Actors are updated rather than created during mouse movement.

The camera guard calculates pitch from camera position and focal point, clamps it to 20–80 degrees, and preserves distance and azimuth. Azimuth is not clamped, allowing continuous 360-degree rotation.

## Terrain and output

The terrain plan uses a small set of Mapzen Terrain Tiles from the AWS Open Data Registry, cached unchanged under `data/raw/terrain/`. A local Hong Kong GeoJSON boundary clips the terrain mesh. Weather rendering and screenshots require no network connection.

The interactive scene and the 24 April screenshot use the same `SceneBuilder`. Automated checks will cover data counts, projection consistency, camera clamping, date-state equality between slider and timer, and fixed colour/height scales. Manual checks will confirm that only one timeline is visible, rotation and pitch limits work, nearest-station text follows the cursor, and highlighting matches the displayed station.
