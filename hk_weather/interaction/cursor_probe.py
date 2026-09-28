"""Zero-plane picking, nearest-station lookup and pointer-following text."""

import time

import numpy as np
from vtkmodules.vtkRenderingCore import vtkCellPicker

from hk_weather.core.config import CURSOR_INTERVAL_S


class CursorProbe:
    def __init__(self, controller):
        self.controller = controller
        self.handles = controller.handles
        self.picker = vtkCellPicker()
        self.picker.SetTolerance(0.0008)
        self.last_pick = 0.0

    def on_mouse_move(self, _caller, _event):
        now = time.monotonic()
        if now - self.last_pick < CURSOR_INTERVAL_S:
            return
        self.last_pick = now
        interactor = self.handles.plotter.iren.interactor
        cursor_x, cursor_y = interactor.GetEventPosition()
        renderer = self.handles.plotter.renderer
        picked = self.picker.Pick(cursor_x, cursor_y, 0, renderer)
        # Both weather surfaces and annotations are non-pickable, so success
        # means a point on land or the invisible Y=0 water pick plane.
        if not picked:
            self.controller.clear_selection()
            return

        world = np.asarray(self.picker.GetPickPosition())
        differences = self.controller.prepared.domain.station_xz - world[[0, 2]]
        station_index = int(np.argmin(np.sum(differences * differences, axis=1)))
        self.controller.select_station(station_index)
        width, height = self.handles.plotter.window_size
        text_width = 305
        text_height = 105
        display_x = cursor_x + 18
        display_y = cursor_y + 18
        if display_x + text_width > width - 95:
            display_x = cursor_x - text_width - 18
        if display_y + text_height > height - 14:
            display_y = cursor_y - text_height - 18
        display_x = int(np.clip(display_x, 8, max(8, width - text_width - 95)))
        display_y = int(np.clip(display_y, 120, max(120, height - text_height - 14)))
        self.handles.cursor_actor.SetDisplayPosition(display_x, display_y)
        self.handles.plotter.render()

    def pulse(self, step):
        if self.controller.selected_station is None:
            return
        scale = 1.0 + 0.12 * np.sin(step * 0.22)
        self.handles.highlight_points_actor.prop.point_size = 15.0 * scale
