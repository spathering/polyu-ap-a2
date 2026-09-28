# Implementation Plan

This plan replaced the elevation-and-columns renderer without changing the validated April 2026 weather dataset.

**Implementation status (28 September 2026):** stages 1–10 are complete and the static viewer is published at [https://spathering.github.io/polyu-ap-a2/](https://spathering.github.io/polyu-ap-a2/). The Python screenshot and interaction, tuned dual surfaces, static payload, VTK.js viewer, production build, artifact validation and Pages workflow have all been tested.

**Interaction/rendering amendment (28 September 2026):** the timeline is now continuous between daily records; autoplay is controlled by a collapsible settings panel; the surfaces fade as they approach `Y=0`; and both renderers apply fragment-depth fog. These changes are verified in the Python scene and a real Edge WebGL session.

**Direction and layout amendment (28 September 2026):** rainfall now rises from `Y=0`, temperature extends below it, and increasing rainfall always maps to greater positive height. The visible sea rectangle has been replaced by a 24-division grid with a major line every fourth interval and radial edge fade. Pitch now spans -60° to +60°. Autoplay no longer discards slow timer frames, and the web settings and legends share one non-overlapping layout rail.

**Temperature-direction amendment (28 September 2026):** the lower temperature mapping is reversed: 28 °C meets `Y=0`, and decreasing temperature produces progressively smaller negative Y. Transparency now also fades at that zero plane rather than at a separate temperature value.

**Timeline-information amendment (28 September 2026):** interpolated positions no longer display fabricated hours. The timeline shows date, 21-station rainfall total and 21-station mean temperature; settings add a `0.25×–3×` speed slider; and a separate source/interpolation panel is collapsed by default.

## 1. Preserve the baseline

- Keep the existing renderer and image recoverable in Git history.
- Record the current audit result and tidy CSV hash.
- Confirm the baseline remains 30 dates, 21 stations and 630 rows.

Gate: the old result can be restored and the data baseline is reproducible.

## 2. Build the flat land/sea base

- Move the current flat-map source and district boundary into the repository's raw-data structure.
- Convert cached terrain tiles into land/sea classification only.
- Render land, sea, coastline and districts at `Y = 0` with no elevation.

Gate: a test image matches the current flat map and contains no relief or contours.

## 3. Build the shared surface domain

- Combine a regular X–Z grid with 21 exact station nodes.
- Create one two-dimensional Delaunay topology.
- Remove unsupported or invalid triangles and record every station node index.

Gate: both future surfaces can share the same nodes and faces, and every station is inside the domain.

## 4. Validate interpolation

- Refactor IDW to support exact matches, k neighbours, configurable power and transforms.
- Use direct IDW for temperature and `log1p` IDW for rainfall.
- Add `tune.py` and compare candidate profiles with leave-one-station-out validation.
- Save the report and fix the chosen settings in configuration.

Gate: all station values are exact, rainfall is never negative, and the parameter choice is reproducible.

## 5. Render one dual-surface frame

- Implement positive rainfall and negative temperature Y mapping.
- Render 24 April with the upper rainfall surface, fading grid, lower temperature surface, station links and two legends.
- Tune transparency, depth peeling, camera distance and visual height.

Gate: viewers can distinguish rainfall above, the zero grid and temperature below without reading code.

## 6. Precompute and animate 30 frames

- Precompute both fields and both Y arrays for every date.
- Replace the old geometry models with `MapDomain` and `FieldFrames`.
- Make `FrameController.apply()` the only date-update path.
- Remove terrain-scalar and rainfall-column updates.

Gate: the scene changes date without rebuilding topology or adding actors, and updates remain below the performance budget.

## 7. Adapt interaction

- Connect autoplay and the single timeline to the new frame controller.
- Add one playback-speed multiplier to the same timer and keep hourly labels out of interpolated states.
- Add a default-collapsed source/interpolation explanation without obscuring the map or timeline.
- Rewrite camera constraints for Y-up rotation.
- Pick only the base map, find the nearest station in X–Z and highlight both surface endpoints.
- Remove elevation from hover text.

Gate: autoplay setting, continuous dragging, 360-degree rotation, -60–60 degree pitch and nearest-station feedback all work together.

## 8. Export a static web payload

- Add thin `build_site.py` and `validate_site.py` entries plus an `hk_weather/web/` adapter.
- Export one shared topology, 30 Float32 temperature/rainfall frames, station values and a versioned manifest.
- Record array shapes, byte order, file sizes and SHA-256 values.
- Stage generated payload files in ignored `web/public/data/` so Vite copies them into `site/data/`.
- Validate the payload against `FieldFrames`, configuration and the 630-row CSV.
- Keep projection, interpolation and height mapping in Python; the exporter only serialises prepared models.

Gate: Python produces a compact, versioned and independently validated static payload without browser code.

## 9. Build and deploy the GitHub Pages viewer

- Add a locked Vite + `@kitware/vtk.js` frontend under `web/`.
- Recreate the three-layer scene from the exported arrays without recalculating IDW.
- Implement the single timeline with date/aggregate summary, autoplay and speed controls, information panel, Y-up camera limits, base picking, nearest-station text and linked highlight in the browser.
- Bundle dependencies locally, set Vite `base` to `./`, and test the `/polyu-ap-a2/` project subpath.
- Keep generated `web/public/data/` and `site/` ignored.
- Add a separate `pages.yml` workflow with read-only build permissions and a Pages/OIDC deployment job.
- Set the repository's Pages source to GitHub Actions and verify the published URL.

Gate: the local HTTP preview and GitHub Pages deployment work without Python, WebSocket, API keys or CDN dependencies.

## 10. Finish and verify

- Generate the final 24 April PNG through the shared scene builder.
- Update README and PROCESS to describe the dual surfaces, rejected old design, static Pages architecture and live URL.
- Remove unused runtime constants and actors while retaining their Git history.
- Run desktop offline checks, site schema/size/path checks, cross-browser review, PEP 723 checks and the assignment checker.

Gate: `uv run plot.py` runs without arguments or network access, the final image exists, and the GitHub Pages project URL preserves the required interaction without a server.
