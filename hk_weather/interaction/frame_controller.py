"""The only code path that applies a date to both field surfaces."""

import numpy as np

from hk_weather.render.station_links import station_link_points


class FrameController:
    """Synchronise both surfaces, station constraints, date and hover text."""

    def __init__(self, weather, prepared, handles):
        self.weather = weather
        self.prepared = prepared
        self.handles = handles
        self.day_index = 0
        self.selected_station = None

    def _station_points(self):
        ids = self.prepared.domain.station_node_ids
        return station_link_points(
            self.prepared.domain.station_xz,
            self.prepared.frames.temperature_y[self.day_index, ids],
            self.prepared.frames.rainfall_y[self.day_index, ids],
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

    def apply(self, day_index):
        self.day_index = int(day_index) % len(self.weather.dates)
        frames = self.prepared.frames
        nodes = self.prepared.domain.nodes_xz

        temperature_points = self.handles.temperature_mesh.points
        temperature_points[:, 0] = nodes[:, 0]
        temperature_points[:, 1] = frames.temperature_y[self.day_index]
        temperature_points[:, 2] = nodes[:, 1]
        self.handles.temperature_mesh.points = temperature_points
        self.handles.temperature_mesh.point_data["temperature_c"] = (
            frames.temperature_c[self.day_index]
        )
        self.handles.temperature_mesh.Modified()

        rainfall_points = self.handles.rainfall_mesh.points
        rainfall_points[:, 0] = nodes[:, 0]
        rainfall_points[:, 1] = frames.rainfall_y[self.day_index]
        rainfall_points[:, 2] = nodes[:, 1]
        self.handles.rainfall_mesh.points = rainfall_points
        self.handles.rainfall_mesh.point_data["rainfall_mm"] = (
            frames.rainfall_mm[self.day_index]
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

        day = self.weather.dates[self.day_index]
        self.handles.date_actor.SetInput(
            f"HONG KONG WEATHER SURFACES  ·  {day.strftime('%d %B %Y').upper()}"
        )
        if self.selected_station is not None:
            self.handles.cursor_actor.SetInput(self.station_text(self.selected_station))
        self.handles.plotter.render()

    def station_text(self, station_index):
        day = self.weather.dates[self.day_index]
        temperature = self.weather.temperatures_c[self.day_index, station_index]
        rainfall = self.weather.rainfall_mm[self.day_index, station_index]
        rain_text = (
            "Trace (<0.05 mm)"
            if self.weather.rainfall_trace[self.day_index, station_index]
            else f"{rainfall:.1f} mm"
        )
        return (
            f"{self.weather.station_names[station_index]} "
            f"({self.weather.station_codes[station_index]})\n"
            f"{day.strftime('%d %b %Y')}\n"
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
