# Hong Kong Weather Surfaces

![Hong Kong weather shown as an upper rainfall surface and lower temperature surface](out/hong-kong-weather-april.png)

## The phenomenon

Hong Kong is geographically small, but its daily weather is not uniform. This project shows how mean temperature and total rainfall varied across 21 observation stations during April 2026.

Hong Kong sits on a fading two-scale reference grid at `Y=0`; major and minor lines become transparent away from the centre. Rainfall forms a continuous surface above it: larger totals rise higher and become darker blue. Temperature forms a second surface below it and changes from purple through orange to yellow. White links show where each measured station constrains the two estimated surfaces.

The scene advances smoothly through all 30 days, linearly interpolating the already spatially interpolated fields between consecutive daily records. A floating draggable timeline accepts continuous positions. A collapsible settings panel contains an automatic-playback checkbox; when selected, the timeline moves automatically. The camera supports 360-degree rotation, zoom, and pitch from -60° below the grid to +60° above it. Moving the pointer over the map shows the nearest station's interpolated date/time, mean temperature and total rainfall, while highlighting both measured endpoints.

## Data and method

The observations come from the Hong Kong Observatory datasets for [daily temperature](https://data.gov.hk/en-data/dataset/hk-hko-rss-daily-temperature-info-hko), [daily total rainfall](https://data.gov.hk/en-data/dataset/hk-hko-rss-daily-total-rainfall), and [weather-station locations](https://www.weather.gov.hk/en/cis/stn.htm). The base uses the official [Hong Kong 18-district boundary](https://www.had.gov.hk/en/public_services/public_data/) and locally cached Mapzen tiles only to distinguish land from sea; geographic elevation is not rendered.

April was selected after auditing every completed month from January to August 2026 across 23 same-site candidates. Shau Kei Wan had two incomplete rainfall records and Wetland Park had one incomplete temperature record, so the final tidy dataset contains 630 complete rows: 21 stations × 30 days. Twelve `Trace` rainfall observations are preserved as trace flags and visualised at 0 mm rather than treated as missing.

Both surfaces share one 18,088-node horizontal topology containing exact station nodes. Temperature uses exact k-nearest inverse-distance weighting (IDW) on Celsius values. Rainfall uses local IDW after a `log1p` transform and is converted back to millimetres. Leave-one-station-out validation selected `power=1.5, k=20` for temperature and `power=2.5, k=8` for rainfall. Fixed month-wide ranges—14–28 °C and 0–67 mm—make dates comparable. Rainfall starts at `Y=0` for 0 mm and rises with rainfall; temperature starts at `Y=0` for 28 °C and descends as temperature becomes lower. For both surfaces, alpha approaches zero as geometry approaches `Y=0`. A fragment-depth shader blends distant screen-space fragments into the background to add depth fog.

The coloured shapes between stations are estimates, not additional measurements. Daily means hide within-day temperature changes, daily totals hide the timing of rain, and surface height is an explanatory visual scale rather than physical altitude. Areas outside the supported Hong Kong land domain are not extrapolated.

## Run the Python version

```bash
uv run plot.py
```

This regenerates `out/hong-kong-weather-april.png` from the same PyVista scene and opens the interactive desktop view. It reads only repository data and needs no network connection.

## Build the static web version

```bash
uv run build_site.py
pnpm --dir web install --frozen-lockfile
pnpm --dir web build
uv run validate_site.py
uv run python -m http.server 8000 --directory site
```

Open `http://127.0.0.1:8000/`. The VTK.js viewer is a fully static client: Python prepares the topology and all 30 frames, then the browser handles rendering and interaction without a server, API key, WebSocket, or CDN.

`.github/workflows/pages.yml` repeats the export, locked frontend build and validation before publishing `site/`. After the repository's Pages source is set to **GitHub Actions** and this work is pushed to `main`, the expected project URL is [https://spathering.github.io/polyu-ap-a2/](https://spathering.github.io/polyu-ap-a2/).
