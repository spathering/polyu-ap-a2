# Technical Plan

## Target architecture

The application is a Python, NumPy, PyVista and VTK project. Its old elevation mesh, temperature drape and rainfall columns have been replaced by a flat land/sea base and two interpolated field surfaces. Existing weather acquisition, auditing and the 630-row tidy dataset remain valid.

The scene is Y-up:

```text
X = projected easting
Z = projected northing
Y = visual data height
```

The base map is fixed at `Y = 0`. Temperature maps to positive Y and rainfall maps to negative Y. PyProj supplies the shared metric projection. Shapely handles the Hong Kong mask and district geometry. Pillow reads the cached Terrarium tiles only to derive a binary land/sea mask; terrain elevation is never rendered. PyVista/VTK provides the shared triangulation, meshes, transparency, camera, picking, timeline, timer and screenshot.

The planned `plot.py` dependency block remains:

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

No SciPy dependency is required. NumPy is sufficient for the 21-station distance matrices and parameter validation, while PyVista/VTK supplies two-dimensional Delaunay triangulation.

## Package layers

```text
hk_weather/
├── app.py
├── core/          configuration, models, paths and timeline state
├── pipeline/      fetch, audit, preparation and interpolation tuning
├── data/          weather, boundary and binary land/sea readers
├── geometry/      projection, domain, IDW, validation and Y mapping
├── render/        base map, field surfaces, station links and legends
├── interaction/   frame controller, timeline, cursor probe and camera guard
└── output/        screenshot generation through the shared scene builder
```

Root `fetch.py`, `audit.py`, `prepare_data.py`, the planned `tune.py`, and `plot.py` remain small PEP 723 entry points. `app.py` is the only module that composes every layer.

Dependencies continue in one direction: `core` is independent; `data` loads validated domain data; `geometry` produces arrays and mesh topology; `render` creates actors; `interaction` updates scene handles; `output` uses the same renderer. Data modules never know about actors, render modules never parse CSV files, and interaction modules never repeat interpolation or projection.

## Shared surface domain

The horizontal domain contains a regular X–Z grid and the exact projected coordinate of each of the 21 stations. A single two-dimensional Delaunay topology is created at `Y = 0`, then triangles outside the supported Hong Kong land domain are removed. The station nodes are recorded explicitly.

The temperature and rainfall meshes copy the same X–Z nodes and faces. Only their Y coordinate and scalar arrays change. This guarantees spatial registration and allows both meshes to be updated without rebuilding topology. The base map is a separate flat mesh covering the current map extent and uses a binary scalar to distinguish land and sea. Coastline and district lines are static overlays.

## Interpolation and validation

`geometry/interpolation.py` will contain one exact k-nearest IDW implementation. It precomputes a target-by-station distance matrix, selects neighbours with NumPy, normalises non-negative weights and uses a one-hot row whenever a target coincides with a station.

Temperature applies the weights directly to Celsius values. Rainfall first applies `log1p`, interpolates the transformed values, then returns to millimetres with `expm1` and clamps round-off below zero. The original values overwrite all station nodes as a final exactness check.

A new thin `tune.py` entry will run leave-one-station-out validation across all 30 dates. Candidate powers are 1.5, 2.0, 2.5 and 3.0; candidate neighbourhoods are 8, 12, 16 and all available training stations. Temperature selection prioritises RMSE and reports MAE. Rainfall selection compares both all-observation MAE and wet-observation MAE. The report is written to `data/derived/interpolation-report.json`; the selected fixed profiles are copied into configuration so rendering never tunes itself at runtime.

## Height mapping and frame data

Height conversion has one implementation in `geometry/height_mapping.py`. Both lower-range baselines map to the middle plane:

```text
temperature_y = Ht × (T - 14) / (28 - 14)
rainfall_y    = -Hr × R / 67
```

`gap`, `Ht` and `Hr` are fractions of the horizontal map span. Both conversions are fixed for the whole month and have inverse functions for legends and tests.

All 30 temperature fields and 30 rainfall fields are computed once at startup. A `FieldFrames` model stores source-unit fields and mapped Y arrays. Runtime changes never recalculate spatial distances or IDW. `FrameController.apply(position)` linearly blends the two neighbouring prepared daily frames, replaces the meshes' Y columns and scalars, updates station links, date/time and hover text, and requests one render.

## Rendering and interaction

The base map is translucent but geographically clear. The upper surface uses a purple-to-orange-to-yellow temperature scale; the lower surface uses a cyan-to-deep-blue rainfall scale and two-sided rendering. Lookup-table alpha follows a smoothstep curve from zero at the 14 °C and 0 mm baselines to each surface's maximum opacity. Depth peeling is enabled when supported. A fragment-shader replacement computes screen-space fog from `gl_FragCoord.z` and blends distant fragments toward the background.

Each station owns a three-point vertical link:

```text
(X, temperature_y, Z) -> (X, 0, Z) -> (X, rainfall_y, Z)
```

The upper and lower endpoints show where the actual observations constrain each surface. Hover picking targets only the zero-plane base. The picked point is compared with station X–Z positions, and one reusable highlight updates the link and both endpoints.

The slider and timer both call the same frame controller with floating positions. A collapsible settings panel controls whether automatic playback advances. Camera maths uses `view_up = (0, 1, 0)`: pitch is clamped to 5–88 degrees while azimuth remains unrestricted. No module may assume that Z is vertical.

## Reuse and replacement

- Reuse: raw weather files, tidy CSV, CSV parsing, completeness audit, paths and most timeline state.
- Adapt: projection, scene composition, screenshot, text, cursor probe, frame controller and camera guard.
- Replace: elevation terrain mesh, terrain renderer and rainfall column renderer.
- Add: flat base map, shared station-aware topology, rainfall interpolation, parameter validation, two field surfaces and Y-axis mapping.

The old output remains in Git history, but the final runtime must not create terrain elevation or rainfall columns.

## Static web architecture

GitHub Pages serves static HTML, CSS, JavaScript and assets; it does not run a Python, Dash or Trame process, as also noted in the GitHub Community [Pages and Python discussion](https://github.com/orgs/community/discussions/166331). The final website will therefore not deploy the desktop PyVista application directly. GitHub's [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) supports building arbitrary static output with Actions and publishing it through `upload-pages-artifact` and `deploy-pages`.

PyVista can [export a scene to HTML](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.plotter.export_html), but that path depends on `trame-pyvista` and is not the contract for this project's custom timer, station probing and linked highlighting. Kitware's [trame architecture discussion](https://github.com/Kitware/trame/discussions/515) notes that trame expects processing on a server; it is not the preferred architecture when most work must run in a scalable client-only page.

The project will instead use a strict producer/viewer split:

```text
Python domain pipeline -> versioned static payload -> VTK.js viewer -> GitHub Pages
```

Python remains authoritative for projection, triangulation, validated interpolation, height mapping, palettes and all 30 frames. A thin `build_site.py` entry calls `hk_weather.web.export` and writes a manifest plus typed-array binary files. The browser never recalculates IDW. It only updates VTK.js PolyData coordinates and scalars from precomputed arrays. VTK.js provides browser-side [PolyData](https://kitware.github.io/vtk-js/docs/structures_PolyData.html), WebGL rendering, picking and animation support.

New source structure:

```text
build_site.py
validate_site.py
hk_weather/web/          payload schema, export and validation
web/                     Vite + @kitware/vtk.js source and package lock
web/public/data/         ignored payload staging generated by Python
site/                    ignored build output
.github/workflows/pages.yml
```

The payload uses one shared X–Z topology, Float32 arrays for 30 temperature and rainfall frames, and JSON metadata for dates, stations, colours, scales and camera rules. `manifest.json` records schema version, shapes, byte order, file size and SHA-256. `build_site.py` writes ignored staging files to `web/public/data/`; Vite copies them into `site/data/`, so generated binary data is not committed and is not erased by the frontend build. This prevents the desktop and website from silently diverging. The initial target is a complete Pages artifact below 20 MB and first-load data below 10 MB, comfortably inside the documented [GitHub Pages limits](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/github-pages-limits).

The web viewer reproduces the continuous timeline, collapsible autoplay setting, Y-up camera, 360-degree azimuth, 5–88 degree pitch, zero-plane picking, nearest-station text, linked endpoint highlight, value-dependent alpha and screen-depth fog. It uses local bundled dependencies rather than a CDN. Vite is configured with `base: "./"`, and every data request is relative, because a project site is served below `/polyu-ap-a2/` rather than the account root.

## Pages workflow

The existing assignment-check workflow remains separate. A new Pages workflow runs on pushes to `main` and manual dispatch:

1. Check out the repository with read-only contents permission.
2. Install pinned uv and Node versions.
3. Run `uv run build_site.py`.
4. Run `pnpm --dir web install --frozen-lockfile` and `pnpm --dir web build`.
5. Run `uv run validate_site.py`.
6. Upload `site/` with `actions/upload-pages-artifact`.
7. In a separate job with `pages: write` and `id-token: write`, deploy with `actions/deploy-pages` to the `github-pages` environment.

The workflow uses the official versioned GitHub Pages actions plus `astral-sh/setup-uv`, `pnpm/action-setup` and `actions/setup-node`. The official [uv GitHub Actions guide](https://docs.astral.sh/uv/guides/integration/github/) recommends `astral-sh/setup-uv` and supports dependency caching. The repository's Settings → Pages source must be set once to **GitHub Actions**.

The generated `web/public/data/` and `site/` directories remain ignored and are not committed. Actions uploads `site/` directly as a Pages artifact. Pull requests build and validate the site without deploying; only `main` or manual dispatch publishes it.

## Web verification

Local verification uses an HTTP server rather than opening `index.html` through `file://`:

```bash
uv run build_site.py
pnpm --dir web install --frozen-lockfile
pnpm --dir web build
uv run validate_site.py
uv run python -m http.server 8000 --directory site
```

Validation checks the schema and checksums, 30 dates, 21 stations, topology size, exact station values, Y signs, artifact size, relative asset paths and absence of CDN dependencies or local absolute paths. Manual browser review covers Chrome, Edge and Firefox, the `/polyu-ap-a2/` project path, autoplay, timeline dragging, picking, camera limits, resize and touch fallback. The deployed Pages URL will be added to README only after the workflow succeeds.

## Verification

Automated checks will verify 30 dates, 21 stations and 630 unique rows; a completely flat base; positive temperature Y; non-positive rainfall Y; exact station hits; finite, non-negative interpolation weights; no negative rain; identical surface topology; fixed scales; equivalent timer and slider state; Y-up camera clamping; and successful off-screen output.

Manual review checks that all three layers remain readable, 24 April produces local rainfall depressions rather than columns, baseline areas fade cleanly, the settings panel collapses, autoplay stops and restarts from its checkbox, fractional dates interpolate, hover highlights both station endpoints, depth fog changes with screen depth, and `uv run plot.py` still works without network access. The Pages build must reproduce the same mappings and interactions without a Python server.
