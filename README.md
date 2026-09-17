# Hong Kong Weather Terrain

![A 3D terrain map of Hong Kong coloured by temperature, with vertical rainfall columns](out/hong-kong-weather-april.png)

> Development status: the source-data pipeline and design are complete. The final PyVista renderer and the image linked above are the next implementation stage.

## The phenomenon

Hong Kong is geographically small, but its daily weather is not uniform. Coastline, dense urban areas, inland valleys, islands and high ground can record different temperatures on the same day, while rainfall can be concentrated around only part of the territory. This project examines those spatial differences across the 30 days of April 2026.

The final picture will be an interactive 3D terrain map. Daily mean temperature will colour the land surface, and daily total rainfall will become a vertical blue column at each observation station. The scene will play through the month automatically. Its only visible control will be a floating, draggable timeline. The camera will allow full 360-degree rotation with its pitch limited to 20–80 degrees. Moving the pointer over the terrain will show the nearest station's values and highlight that station.

## The source

The weather observations come from the Hong Kong Observatory's public datasets for [daily maximum, mean and minimum temperature](https://data.gov.hk/en-data/dataset/hk-hko-rss-daily-temperature-info-hko), [daily total rainfall](https://data.gov.hk/en-data/dataset/hk-hko-rss-daily-total-rainfall), and [weather-station locations](https://www.weather.gov.hk/en/cis/stn.htm). The raw responses are stored unchanged under `data/raw/`; the scripts do not repeatedly request them.

I audited 23 stations that publish both measurements at the same site across every completed month from January to August 2026. April had the best coverage. Shau Kei Wan contained two incomplete rainfall records and Wetland Park contained one incomplete temperature record, so the final dataset uses the remaining 21 complete stations.

`data/hk-weather-2026-04.csv` contains 630 rows: 21 stations × 30 days. Each row represents one station on one date and contains station code and name, latitude and longitude, station elevation in metres, daily mean temperature in degrees Celsius, daily total rainfall in millimetres, and a Boolean trace-rainfall marker. All 630 temperature and 630 rainfall source records carry the HKO `C` completeness flag. Twelve rainfall observations are `Trace`, meaning less than 0.05 mm; they remain identifiable instead of being treated as missing values.

The planned terrain layer will use locally cached [Mapzen Terrain Tiles from the AWS Open Data Registry](https://registry.opendata.aws/terrain-tiles/) and a locally stored Hong Kong boundary. Rendering will remain available without a network connection.

## What the picture shows

Temperature is interpolated between observation stations with inverse-distance weighting and displayed with one fixed 14–28 °C colour scale. Rainfall uses one fixed linear 0–67 mm column-height scale. Keeping both scales fixed makes changes between dates comparable. The README image will use 24 April, the day with the highest summed rainfall across the 21 stations.

The coloured areas between stations are estimates, not measurements at every location. Daily mean temperature hides the day-night cycle, and daily rainfall hides the time and intensity of individual showers. Terrain height represents geography, but rainfall-column height is deliberately exaggerated as a visual scale and must not be read as physical altitude.

## Run it

```bash
uv run plot.py
```
