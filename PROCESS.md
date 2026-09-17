# Process

## Tools

I used OpenAI Codex to read the assignment brief and week 3 teaching material, investigate public data sources, write and revise the acquisition and audit scripts, plan the visual design, and reorganise the Python code. I directed the subject choice and progressively specified the intended interaction: a real 3D terrain map, temperature as surface colour, rainfall as height, 20–80 degree camera pitch, unrestricted rotation, one floating timeline, and nearest-station information that follows the pointer.

Python and `uv` were used to fetch the Hong Kong Observatory files once, inspect their raw CSV structure, compare completed months, validate the selected period and generate the tidy dataset. The source responses were kept byte-for-byte under `data/raw/`. After restructuring the code, I reran the audit and preparation scripts and compared the generated CSV hash to confirm that the refactor had not changed the result.

Web research was limited to primary or clearly attributed sources: Hong Kong Observatory and DATA.GOV.HK pages for weather data, CEDD maps for visual research, official PyVista documentation for 3D interaction capabilities, geoBoundaries for a planned land boundary, and the AWS Open Data Registry for a compact terrain source. Reference pictures are kept outside this repository in the working-material folder. They are design references only and will not be copied into the final visualisation.

## Kept

I kept the recommendation to use daily rather than hourly data. The free HKO interfaces provide suitable historical daily measurements from multiple stations, while their free short-interval interfaces mainly provide current snapshots. Daily data also produces a clear 30-frame timeline that is small enough to inspect carefully.

I kept the 2026 April selection only after testing it. The audit compared January through August across 23 same-site candidate station pairs. April had 21 complete pairs, more than any other completed month. Removing Shau Kei Wan and Wetland Park preserved all 30 dates and produced 630 complete date-station rows without duplicates or blanks.

I kept `Trace` rainfall as a real observation. An early version of the audit incorrectly reported the word `Trace` as invalid numeric data. Reading the note in the HKO rainfall files showed that it means rainfall below 0.05 mm. The corrected pipeline stores 0.0 mm for rendering and a separate `rainfall_trace=true` field so the original meaning remains available in the interface.

I also kept the separation between direct observations and visual transformation. Station temperature is measured, but the continuous colour surface is inverse-distance interpolation. Rainfall is measured in millimetres, but the 3D column height is an explicitly exaggerated visual scale. These limits are stated in the README instead of being hidden.

Finally, I kept the modular package proposal. Acquisition, auditing and preparation now live under `hk_weather/core/` and `hk_weather/pipeline/`; root scripts are only PEP 723 entry points. The final renderer will continue this structure with separate data, geometry, rendering, interaction and output layers. A single frame controller will update temperature, rain, date text and nearest-station text for both automatic playback and timeline dragging.

## Rejected

The first research note proposed a full 2025 dataset of roughly 24 stations. I rejected it after the assignment scope and current data were examined. A complete current-year month is easier to verify, has enough temporal change for animation, and avoids turning a small visualisation assignment into a large archive project.

I rejected the first July 2026 download as the final period. July had only 17 fully complete candidate pairs. April had 21, so it provides better spatial coverage. I also rejected Kai Tak and Tsing Yi before the month audit because the temperature and rainfall resources refer to different station codes or physical sites; matching by a similar name would have created false paired observations.

The first interaction plan used Plotly in a self-contained HTML page, with Matplotlib producing a separate still. I rejected that architecture after defining the final interaction. Strict camera-angle limits, continuous terrain picking, text following the cursor, and a reusable pulsing station highlight are more direct in PyVista/VTK. PyVista can also create the required PNG from the same scene builder, avoiding two separate rendering implementations.

I rejected the Hong Kong Lands Department's complete 5 m terrain model as the main repository asset because the published whole-territory file is about 290 MB. The current plan uses a small number of open terrain tiles covering only Hong Kong, cached once and downsampled for the scene.

I also rejected a single large `plot.py`. Projection, interpolation, terrain construction, actor creation, camera limits, timeline state and cursor picking have different responsibilities. Keeping them in one file would duplicate basic transformations and make interaction changes likely to break the static output.

## Current status

The weather acquisition, audit, tidy CSV, design and initial package refactor are complete. The current `hk_weather/app.py` still contains the untouched template renderer and is intentionally identified as temporary. The terrain acquisition and PyVista scene described in `DESIGN.md` and `TECHNICAL.md` have not yet been implemented. This section should be replaced with final testing notes before submission.
