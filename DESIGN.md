# Design: Hong Kong Weather Surfaces

## Visual idea

The revised work uses the current flat Hong Kong land-and-sea map as its zero plane. It no longer visualises real terrain elevation. Daily observations from 21 weather stations generate two continuous surfaces for every day of April 2026:

- temperature rises above the map on the positive Y axis;
- rainfall extends below the map on the negative Y axis;
- the flat map remains at `Y = 0` and distinguishes land, sea, coastline and district boundaries.

The main visual statement is that Hong Kong's temperature forms a broad, slowly changing field, while rainfall forms more local and abrupt depressions. Measured station values are shown as endpoints connected through the zero plane. Every point between stations is explicitly an interpolation rather than a direct observation.

## Coordinate and visual mapping

The scene uses Y as its only height axis. Projected easting becomes X, projected northing becomes Z, and every base-map vertex has `Y = 0`. Station longitude and latitude therefore remain aligned across the base, temperature surface and rainfall surface.

Temperature uses one fixed 14–28 °C scale for the whole month. Its 14 °C baseline lies exactly on the map plane and warmer values rise higher. Rainfall uses a 0 mm baseline on the same plane and larger totals extend downward. Alpha approaches zero near each baseline, so low-signal regions dissolve into the middle plane instead of forming opaque sheets. The upper surface uses a purple-to-orange-to-yellow colour scale so it remains distinct from blue rainfall.

Rainfall uses one fixed 0–67 mm scale. Zero rain meets the base plane; increasing rain extends farther down. The lower surface uses a pale-cyan-to-deep-blue scale. The two height conversions are linear but independent because °C and mm are different units. Legends always show the original units rather than suggesting that scene height is physical altitude.

The base map uses muted green land and pale blue sea. It is translucent enough for the lower rainfall surface to remain visible, while coastline and district lines preserve geographic orientation. There is no hillshade, contour line or terrain exaggeration.

## Surface interpolation

Both surfaces share one triangulated horizontal domain. The domain contains a regular map grid plus the exact X–Z position of every station, so each station is a real mesh node rather than an approximate nearest grid point.

Temperature is estimated with exact k-nearest inverse-distance weighting (IDW) on the original Celsius values. Rainfall is non-negative, highly skewed and often zero, so it uses local IDW after a `log1p` transform and returns to millimetres with `expm1`. An exact-match rule forces both surfaces through the original station values and prevents zero or trace rainfall from being changed at a station.

The power and neighbour count are not chosen only by appearance. Candidate settings are compared across all 30 days with leave-one-station-out validation. Temperature is evaluated with RMSE and MAE. Rainfall is evaluated with overall MAE and wet-observation MAE so that dry records do not dominate the choice. One fixed setting per variable is then used for the whole month.

## Interaction

The main control is a floating continuous timeline. The scene starts at 1 April, advances one data-day in about 900 ms and loops after 30 April. Geometry, scalar colours, station links and tooltip values are linearly interpolated between consecutive daily records; the time label includes hours and minutes so estimated in-between states cannot be mistaken for new observations. A small collapsible floating settings panel exposes automatic playback, enabled by default.

The camera can rotate through a full 360 degrees around the Y axis, zoom with the mouse wheel, and change pitch between 5 and 88 degrees. The initial view is 30 degrees so the upper surface, zero plane and lower surface can all be read together. Screen-space depth fog uses fragment depth to blend distant geometry toward the background, strengthening depth without encoding another measurement.

Moving the pointer over the flat map identifies the nearest station in the X–Z plane. Text follows the pointer and shows station name, date, mean temperature and rainfall or `Trace (<0.05 mm)`. The station's upper endpoint, lower endpoint and connecting line highlight together. Elevation is removed from this text because the revised work does not visualise geographic height.

## Still image and limits

The README still uses 24 April, the day with the highest summed rainfall across the 21 complete stations. The still and interactive window must use the same scene builder, scales, interpolation profiles and Y-up camera rules.

The surfaces estimate conditions between a limited number of stations. They do not reconstruct local weather at street scale. Daily means hide within-day temperature changes, daily totals hide the time of rain, and the visual height is a fixed display mapping rather than physical altitude. Areas without adequate station support are excluded instead of being presented as confident long-distance extrapolation.

## Acceptance criteria

- The base is flat and clearly separates land from sea.
- Temperature stays above `Y = 0`; rainfall stays at or below it.
- Both surfaces hit every station's value for every date.
- All dates use fixed height and colour scales.
- The upper surface, base map and lower surface remain legible in the 24 April still.
- Autoplay toggle, continuous timeline, 360-degree rotation, 5–88 degree pitch and nearest-station highlight all remain available.
