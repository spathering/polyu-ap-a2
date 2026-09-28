"""The only code path that applies a date to both field surfaces."""

from datetime import datetime, time, timedelta

import numpy as np

from hk_weather.render.station_links import station_link_points


class FrameController:
    """Synchronise both surfaces, station constraints, date and hover text."""

    def __init__(self, weather, prepared, handles):
        self.weather = weather
        self.prepared = prepared
        self.handles = handles
        self.position = 0.0
        self.day_index = 0
        self.selected_station = None

    def _frame_indices(self):
        lower = int(np.floor(self.position))
        upper = min(lower + 1, len(self.weather.dates) - 1)
        return lower, upper, self.position - lower

    def _blend(self, values):
        lower, upper, fraction = self._frame_indices()
        if lower == upper or fraction <= 1e-9:
            return values[lower]
        return values[lower] * (1.0 - fraction) + values[upper] * fraction

    def _display_datetime(self):
        start = datetime.combine(self.weather.dates[0], time.min)
        return start + timedelta(days=self.position)

    def _station_points(self):
        ids = self.prepared.domain.station_node_ids
        return station_link_points(
            self.prepared.domain.station_xz,
            self._blend(self.prepared.frames.temperature_y)[ids],
            self._blend(self.prepared.frames.rainfall_y)[ids],
        )

    def _update_highlight(self, station_points):
        if self.selected_station is None:
            self.handles.highlight_actor.visibility = False
            self.handles.highlight_points_actor.visibility = False
            return
        start = self.selected_station * 3
        selected = station_points[start : start + 3]
        self.handles.highlight_mesh.points = selected
        self.handles.highlight_mesh.Modified()
        self.handles.highlight_points_mesh.points = selected[[0, 2]]
        self.handles.highlight_points_mesh.Modified()
        self.handles.highlight_actor.visibility = True
        self.handles.highlight_points_actor.visibility = True

    def apply(self, position):
        self.position = float(
            np.clip(position, 0.0, len(self.weather.dates) - 1)
        )
        lower, _, _ = self._frame_indices()
        self.day_index = lower
        frames = self.prepared.frames
        nodes = self.prepared.domain.nodes_xz
        temperature_y = self._blend(frames.temperature_y)
        temperature_c = self._blend(frames.temperature_c)
        rainfall_y = self._blend(frames.rainfall_y)
        rainfall_mm = self._blend(frames.rainfall_mm)

        temperature_points = self.handles.temperature_mesh.points
        temperature_points[:, 0] = nodes[:, 0]
        temperature_points[:, 1] = temperature_y
        temperature_points[:, 2] = nodes[:, 1]
        self.handles.temperature_mesh.points = temperature_points
        self.handles.temperature_mesh.point_data["temperature_c"] = (
            temperature_c
        )
        self.handles.temperature_mesh.Modified()

        rainfall_points = self.handles.rainfall_mesh.points
        rainfall_points[:, 0] = nodes[:, 0]
        rainfall_points[:, 1] = rainfall_y
        rainfall_points[:, 2] = nodes[:, 1]
        self.handles.rainfall_mesh.points = rainfall_points
        self.handles.rainfall_mesh.point_data["rainfall_mm"] = (
            rainfall_mm
        )
        self.handles.rainfall_mesh.Modified()

        station_points = self._station_points()
        self.handles.station_link_mesh.points = station_points
        self.handles.station_link_mesh.Modified()
        endpoint_ids = np.asarray(
            [
                index * 3 + endpoint
                for index in range(len(self.prepared.domain.station_xz))
                for endpoint in (0, 2)
            ]
        )
        self.handles.station_endpoint_mesh.points = station_points[endpoint_ids]
        self.handles.station_endpoint_mesh.Modified()
        self._update_highlight(station_points)

        moment = self._display_datetime()
        self.handles.date_actor.SetInput(
            "HONG KONG WEATHER SURFACES  ·  "
            f"{moment.strftime('%d %B %Y · %H:%M').upper()}"
        )
        if self.selected_station is not None:
            self.handles.cursor_actor.SetInput(self.station_text(self.selected_station))
        self.handles.plotter.render()

    def station_text(self, station_index):
        moment = self._display_datetime()
        lower, upper, fraction = self._frame_indices()
        temperature = float(self._blend(self.weather.temperatures_c)[station_index])
        rainfall = float(self._blend(self.weather.rainfall_mm)[station_index])
        exact_trace = (
            fraction <= 1e-9 and self.weather.rainfall_trace[lower, station_index]
        ) or (
            1.0 - fraction <= 1e-9
            and self.weather.rainfall_trace[upper, station_index]
        )
        rain_text = (
            "Trace (<0.05 mm)"
            if exact_trace
            else f"{rainfall:.1f} mm"
        )
        return (
            f"{self.weather.station_names[station_index]} "
            f"({self.weather.station_codes[station_index]})\n"
            f"{moment.strftime('%d %b %Y · %H:%M')}\n"
            f"Mean temperature  {temperature:.1f} °C\n"
            f"Total rainfall       {rain_text}"
        )

    def select_station(self, station_index):
        self.selected_station = int(station_index)
        self._update_highlight(self._station_points())
        self.handles.cursor_actor.SetInput(self.station_text(self.selected_station))
        self.handles.cursor_actor.SetVisibility(True)

    def clear_selection(self):
        self.selected_station = None
        self.handles.highlight_actor.visibility = False
        self.handles.highlight_points_actor.visibility = False
        self.handles.cursor_actor.SetVisibility(False)
