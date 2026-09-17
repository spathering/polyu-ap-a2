# Design: Hong Kong Weather Terrain

## Visual idea

The work will render a real 3D terrain map of Hong Kong for every day of April 2026. Temperature is interpolated from 21 complete weather stations and mapped to the terrain colour. Daily rainfall becomes a translucent vertical column at each station. The visual message is that temperature forms a broad spatial field while rain often appears as a much more local event.

The initial camera pitch is about 45 degrees. Users can rotate around the map through a full 360 degrees, zoom with the mouse wheel, and change pitch only between 20 and 80 degrees. Roads, buildings and commercial map labels are omitted so the coastline, islands, terrain and weather remain dominant.

## Visual mapping

- Station longitude and latitude determine horizontal position.
- Local elevation data creates the terrain mesh; temperature colour is draped over that mesh.
- Temperature uses inverse-distance weighting and one fixed 14–28 °C scale for the whole month.
- Rainfall uses column height and one fixed linear 0–67 mm scale.
- A trace observation is displayed as `Trace (<0.05 mm)`, not as missing data.
- Station elevation appears in information text but is not added to rainfall height.

## Interaction

The only visible control is a floating timeline along the bottom of the 3D window. It contains 30 discrete dates. The scene starts playing automatically, advances about once per second and loops after 30 April. Dragging the timeline pauses automatic updates and changes the terrain colour, rainfall columns and date immediately. About two seconds after release, playback continues from the selected date. There are no play, pause, reset or layer buttons.

Moving the mouse anywhere over the Hong Kong terrain identifies the nearest station. Text follows the cursor and shows station name, date, mean temperature, rainfall and station elevation. The corresponding station gains a bright halo and subtle pulse, and its rainfall column becomes brighter. The text and highlight disappear when the pointer leaves the map.

The README still will use 24 April, the day with the highest summed rainfall across the 21 stations. The still and interactive window will be built from the same scene code and use the same scales and camera rules.

## Limits

The coloured surface between stations is an estimate rather than a direct observation. Daily values hide hourly temperature and rainfall variation. Terrain height is geographically meaningful, but rainfall column height is a visual scale and must not be read as physical altitude.
