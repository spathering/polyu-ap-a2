"""One floating slider and the automatic date player."""

import time

from hk_weather.core.config import AUTOPLAY_INTERVAL_S, AUTOPLAY_RESUME_DELAY_S


class TimelinePlayer:
    def __init__(self, controller):
        self.controller = controller
        self.widget = None
        self.dragging = False
        self.resume_at = 0.0
        self.last_advance = time.monotonic()

    def slider_changed(self, value):
        self.controller.apply(round(value))

    def drag_started(self, _widget, _event):
        self.dragging = True

    def drag_ended(self, _widget, _event):
        self.dragging = False
        self.resume_at = time.monotonic() + AUTOPLAY_RESUME_DELAY_S
        self.last_advance = time.monotonic()

    def on_timer(self, _step):
        now = time.monotonic()
        if self.dragging or now < self.resume_at:
            return
        if now - self.last_advance < AUTOPLAY_INTERVAL_S:
            return
        next_day = (self.controller.day_index + 1) % len(self.controller.weather.dates)
        self.controller.apply(next_day)
        self.widget.GetRepresentation().SetValue(next_day)
        self.last_advance = now


def add_timeline(plotter, controller, interactive=True):
    """Add the application's only visible control."""
    player = TimelinePlayer(controller)
    widget = plotter.add_slider_widget(
        player.slider_changed,
        rng=(0, len(controller.weather.dates) - 1),
        value=controller.day_index,
        title="APRIL 2026",
        pointa=(0.16, 0.075),
        pointb=(0.80, 0.075),
        style="modern",
        interaction_event="always",
        tube_width=0.006,
        slider_width=0.018,
        title_height=0.018,
        fmt="%0.0f",
    )
    player.widget = widget
    representation = widget.GetRepresentation()
    representation.SetShowSliderLabel(False)
    widget.AddObserver("StartInteractionEvent", player.drag_started)
    widget.AddObserver("EndInteractionEvent", player.drag_ended)
    if interactive:
        plotter.add_timer_event(
            max_steps=10_000_000,
            duration=50,
            callback=player.on_timer,
        )
    return player
