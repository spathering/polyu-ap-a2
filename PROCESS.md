# Process

## Tools and source handling

I used OpenAI Codex to read the brief and week 3 material, investigate public sources, audit candidate periods, restructure the code, and test the desktop and static-web outputs. I directed the subject and progressively changed the visual brief. Python and `uv` handle acquisition, checking, interpolation, geometry and PyVista rendering. Vite, pnpm and VTK.js create the static browser version. GitHub Actions is configured only for reproducible build and Pages deployment.

The acquisition script stores source responses unchanged under `data/raw/` and skips files already present. Runtime scripts read only local files. The selected tidy file was regenerated after refactors and retained the same 630 unique date–station rows. Web research was restricted to attributed sources: HKO/DATA.GOV.HK for observations, the Hong Kong government for district boundaries, AWS Open Data for cached Mapzen tiles, and official GitHub, uv, PyVista and Kitware documentation for deployment decisions.

## Kept decisions

I kept daily data rather than trying to fabricate an hourly history. HKO's free historical station files provide complete daily observations, while its free short-interval interfaces are mainly current snapshots. A 30-frame month is also small enough to verify and legible on one timeline.

April 2026 was kept only after comparing January–August across 23 candidate temperature/rainfall station pairs. April supplied 21 complete pairs, more than any other completed month. Excluding the two incomplete stations preserved every day and produced 630 rows with no duplicate keys, missing values or incomplete source flags.

`Trace` rainfall was kept as a valid observation. It means less than 0.05 mm, not missing data. The tidy dataset stores 0.0 mm for rendering and a separate Boolean trace flag, and the hover label restores its meaning.

The flat map and two surfaces use one Y-up coordinate convention. Station positions are exact nodes in the shared topology; temperature is always above `Y=0`, rainfall is at or below it, and both are forced through the original observations. One frame controller updates geometry, colours, station links, date and tooltip for autoplay and timeline input, so those paths cannot drift apart.

I kept separate desktop and browser renderers but not separate data logic. Python remains authoritative for projection, topology, tuned interpolation, height mapping and every frame. The static viewer consumes a versioned binary payload and performs no scientific recomputation. That producer/viewer boundary is what makes GitHub Pages possible without weakening the Python implementation.

## Rejected and revised decisions

The first concept covered a complete year and used a Plotly heat surface with rainfall columns. I rejected the year after inspecting the assignment scale and rejected Plotly when strict camera limits, continuous picking and linked highlights became requirements.

The next implementation used real terrain elevation, temperature colour on the terrain, and one vertical rainfall column per station. It worked, but it no longer matched the revised visual argument. Elevation competed with temperature for height, and isolated columns did not describe rainfall distribution between stations. The final design therefore removes geographic height: a flat land/sea plane separates a positive temperature surface from a negative rainfall surface.

I also rejected choosing interpolation settings by appearance alone. Leave-one-station-out tests across all 630 observations selected the fixed parameters now recorded in `data/derived/interpolation-report.json`. Rainfall is interpolated in `log1p` space to reduce the spatial dominance of extreme totals while remaining non-negative after inversion.

PyVista's HTML export and a live Trame application were considered for deployment. They were rejected because GitHub Pages cannot execute a persistent Python service, and the project's timer, picking and linked highlight should not depend on an assumed callback conversion. A static VTK.js client with precomputed arrays is smaller, explicit and compatible with a project-site subpath.

## Implementation and corrections

The final Python package separates `core`, `pipeline`, `data`, `geometry`, `render`, `interaction`, `output` and `web` responsibilities. Root scripts are thin PEP 723 entry points. The scene contains a flat land/sea base, district outlines, two shared-topology surfaces and reusable station links; date changes modify arrays rather than rebuilding actors.

The first dual-surface draft used overlapping blue palettes. Visual review showed that the layers were hard to distinguish, so temperature changed to purple–orange–yellow while rainfall remained cyan–blue. Increasing the map-domain resolution to 18,088 nodes reduced blockiness without exceeding the static-site budget. The initial browser run also exposed two API assumptions: VTK.js did not provide `setRenderPointsAsSpheres` on the current property object, and the generic render window did not expose `getOpenGLRenderWindow`. Removing the optional sphere hint and using the canvas pixel dimensions fixed startup and picking.

The final 24 April screenshot comes from the same Python scene used by the desktop interaction. The web payload records schema version, array shapes, byte order, file sizes and SHA-256 hashes. Generated staging data and `site/` are ignored; the workflow recreates and validates them rather than committing build output.

## Verification status

- Weather audit: 30 dates, 21 stations, 630 unique complete rows.
- Interpolation: exact station hits, finite weights, non-negative rainfall, fixed scales.
- Desktop: off-screen PNG generation succeeds with 18,088 shared nodes.
- Static export: the complete Pages artifact validates at 9.6 MB.
- Frontend: Vite production build transforms 351 modules successfully.
- Browser: Edge loaded the served build with one WebGL canvas, autoplay advanced dates, dragging selected 24 April, and hover picking displayed and highlighted the nearest station without runtime errors.
- Deployment: `.github/workflows/pages.yml` is ready; publishing still requires the repository's one-time Pages source setting and a push to `main`.
