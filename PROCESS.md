# Process

## Tools and source handling

I used OpenAI Codex to read the brief and week 3 material, investigate public sources, audit candidate periods, restructure the code, and test the desktop and static-web outputs. I directed the subject and progressively changed the visual brief. Python and `uv` handle acquisition, checking, interpolation, geometry and PyVista rendering. Vite, pnpm and VTK.js create the static browser version. GitHub Actions is configured only for reproducible build and Pages deployment.

The acquisition script stores source responses unchanged under `data/raw/` and skips files already present. Runtime scripts read only local files. The selected tidy file was regenerated after refactors and retained the same 630 unique date–station rows. Web research was restricted to attributed sources: HKO/DATA.GOV.HK for observations, the Hong Kong government for district boundaries, AWS Open Data for cached Mapzen tiles, and official GitHub, uv, PyVista and Kitware documentation for deployment decisions.

## Kept decisions

I kept daily data rather than trying to fabricate an hourly history. HKO's free historical station files provide complete daily observations, while its free short-interval interfaces are mainly current snapshots. A 30-frame month is also small enough to verify and legible on one timeline.

April 2026 was kept only after comparing January–August across 23 candidate temperature/rainfall station pairs. April supplied 21 complete pairs, more than any other completed month. Excluding the two incomplete stations preserved every day and produced 630 rows with no duplicate keys, missing values or incomplete source flags.

`Trace` rainfall was kept as a valid observation. It means less than 0.05 mm, not missing data. The tidy dataset stores 0.0 mm for rendering and a separate Boolean trace flag, and the hover label restores its meaning.

The flat map and two surfaces use one Y-up coordinate convention. Station positions are exact nodes in the shared topology; rainfall is at or above `Y=0`, temperature is at or below it, and both are forced through the original observations. One frame controller updates geometry, colours, station links, date and tooltip for autoplay and timeline input, so those paths cannot drift apart.

I kept separate desktop and browser renderers but not separate data logic. Python remains authoritative for projection, topology, tuned interpolation, height mapping and every frame. The static viewer consumes a versioned binary payload and performs no scientific recomputation. That producer/viewer boundary is what makes GitHub Pages possible without weakening the Python implementation.

## Rejected and revised decisions

The first concept covered a complete year and used a Plotly heat surface with rainfall columns. I rejected the year after inspecting the assignment scale and rejected Plotly when strict camera limits, continuous picking and linked highlights became requirements.

The next implementation used real terrain elevation, temperature colour on the terrain, and one vertical rainfall column per station. It worked, but it no longer matched the revised visual argument. Elevation competed with temperature for height, and isolated columns did not describe rainfall distribution between stations. Geographic height was therefore removed in favour of a shared zero reference and two data surfaces; the final orientation puts rainfall above and temperature below that reference.

I also rejected choosing interpolation settings by appearance alone. Leave-one-station-out tests across all 630 observations selected the fixed parameters now recorded in `data/derived/interpolation-report.json`. Rainfall is interpolated in `log1p` space to reduce the spatial dominance of extreme totals while remaining non-negative after inversion.

PyVista's HTML export and a live Trame application were considered for deployment. They were rejected because GitHub Pages cannot execute a persistent Python service, and the project's timer, picking and linked highlight should not depend on an assumed callback conversion. A static VTK.js client with precomputed arrays is smaller, explicit and compatible with a project-site subpath.

## Implementation and corrections

The final Python package separates `core`, `pipeline`, `data`, `geometry`, `render`, `interaction`, `output` and `web` responsibilities. Root scripts are thin PEP 723 entry points. The scene contains flat land, a fading two-scale grid, district outlines, two shared-topology surfaces and reusable station links; date changes modify arrays rather than rebuilding actors.

The first dual-surface draft used overlapping blue palettes. Visual review showed that the layers were hard to distinguish, so temperature changed to purple–orange–yellow while rainfall remained cyan–blue. Increasing the map-domain resolution to 18,088 nodes reduced blockiness without exceeding the static-site budget. The initial browser run also exposed two API assumptions: VTK.js did not provide `setRenderPointsAsSpheres` on the current property object, and the generic render window did not expose `getOpenGLRenderWindow`. Removing the optional sphere hint and using the canvas pixel dimensions fixed startup and picking.

The final 24 April screenshot comes from the same Python scene used by the desktop interaction. The web payload records schema version, array shapes, byte order, file sizes and SHA-256 hashes. Generated staging data and `site/` are ignored; the workflow recreates and validates them rather than committing build output.

The later interaction pass changed the timeline from 30 hard steps to a continuous position. Spatial IDW remains precomputed only on the 30 real days; runtime code linearly blends adjacent prepared fields and labels intermediate states with an explicit time. I added a collapsible settings panel instead of another permanently visible control, and its checked automatic-playback option is now the sole source of playback state. Smooth alpha ramps suppress both surfaces close to `Y=0`, and a fragment-depth shader supplies screen-space fog in both renderers.

The final orientation pass moved rainfall to positive Y and temperature to negative Y so increased rainfall reads directly as increased height. Camera pitch was widened across the reference plane to -60–60°. The opaque sea rectangle was removed and replaced visually by minor and major grid lines whose alpha fades radially; an invisible rectangle remains only as the water picking target. The web settings and legends now flow in one right-hand rail, and pointer text avoids both that rail and the timeline. Desktop autoplay was corrected so long render frames are capped rather than discarded.

The temperature height mapping was then reversed inside the negative half-space: 28 °C is the zero-height anchor, and colder observations move farther downward. Transparency was aligned with geometry so the temperature surface now fades at 28 °C / `Y=0`; the fixed colour range and interpolation remain unchanged.

## Verification status

- Weather audit: 30 dates, 21 stations, 630 unique complete rows.
- Interpolation: exact station hits, finite weights, non-negative rainfall, fixed scales.
- Desktop: off-screen PNG generation succeeds with 18,088 shared nodes.
- Static export: the complete Pages artifact validates at 9.6 MB.
- Frontend: Vite production build transforms 351 modules successfully.
- Browser: Edge loaded the served build with one WebGL canvas and no runtime errors. In 754 × 440 and narrow 492 × 704 viewports, the open settings panel, both legends, title, date, timeline and footer had no intersecting rectangles. Autoplay advanced from 8.13 to 9.39 in 1.1 seconds, held exactly at 9.39 while unchecked, and resumed to 10.58 after re-enabling. Hover picking retained interpolated station values and linked highlighting over land and the invisible water pick plane.
- Deployment: `.github/workflows/pages.yml` is ready; publishing still requires the repository's one-time Pages source setting and a push to `main`.
- CI correction: the first Pages run could not resolve the non-existent floating `astral-sh/setup-uv@v10` tag. The workflow now pins setup-uv v10.2.0 to its immutable full commit SHA, following the action's security guidance.
- Pages enablement: a later run built and validated the complete site but `configure-pages` returned `404 Not Found` because the repository had no enabled Pages site. The build job now has least-privilege `pages: read`; the repository owner must still select **Settings → Pages → Build and deployment → Source: GitHub Actions** once, then rerun the failed workflow. Automatic `enablement: true` was not used because it requires a PAT or GitHub App token rather than the default `GITHUB_TOKEN`.
