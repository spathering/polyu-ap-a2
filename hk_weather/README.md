# `hk_weather` package

All substantive Python implementation lives here; root scripts are small PEP 723 entry points.

- `core/`: configuration, paths and shared data/geometry models.
- `pipeline/`: one-time fetch, audit, tidy-data preparation and interpolation tuning.
- `data/`: validated weather, official district and binary land/sea readers.
- `geometry/`: projection, station-aware shared topology, exact k-nearest IDW, height mapping and invariants.
- `render/`: flat base, fading upper/lower field surfaces, screen-depth fog, station links, text and shared PyVista scene.
- `interaction/`: continuous between-day frame blending, collapsible autoplay settings, timeline, Y-up camera guard and nearest-station probing.
- `output/`: off-screen PNG generation from the shared desktop scene.
- `web/`: versioned static-payload export and validation for the VTK.js client.

`app.py` is the only module that composes data, geometry, rendering and interaction. The browser never repeats projection or interpolation: `build_site.py` serialises the prepared models, and `web/src/main.js` only renders and updates those arrays.
