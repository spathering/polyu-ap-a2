"""Clamp camera pitch while leaving azimuth and zoom unrestricted."""

import math

import numpy as np

from hk_weather.core.config import CAMERA_PITCH_RANGE_DEG


class CameraGuard:
    def __init__(self, plotter):
        self.plotter = plotter
        self.adjusting = False

    def enforce(self, _caller, _event):
        if self.adjusting:
            return
        camera = self.plotter.camera
        position = np.asarray(camera.position, dtype=float)
        focal = np.asarray(camera.focal_point, dtype=float)
        offset = position - focal
        distance = float(np.linalg.norm(offset))
        horizontal_vector = offset[[0, 2]]
        horizontal = float(np.linalg.norm(horizontal_vector))
        if distance == 0.0:
            return
        pitch = math.degrees(math.atan2(offset[1], horizontal))
        clamped = min(max(pitch, CAMERA_PITCH_RANGE_DEG[0]), CAMERA_PITCH_RANGE_DEG[1])
        if abs(clamped - pitch) < 0.05:
            return
        if horizontal < 1e-6:
            direction = np.array([1.0, 0.0])
        else:
            direction = horizontal_vector / horizontal
        radians = math.radians(clamped)
        new_offset = np.array(
            [
                direction[0] * distance * math.cos(radians),
                distance * math.sin(radians),
                direction[1] * distance * math.cos(radians),
            ]
        )
        self.adjusting = True
        camera.position = tuple(focal + new_offset)
        camera.up = (0.0, 1.0, 0.0)
        self.adjusting = False
