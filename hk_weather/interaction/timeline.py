"""One floating slider and the automatic date player."""

import time

from hk_weather.core.config import AUTOPLAY_INTERVAL_S, AUTOPLAY_RESUME_DELAY_S


class TimelinePlayer:
    def __init__(self, controller):
        self.controller = controller
        self.widget = None
        self.dragging = False
        self.autoplay = True
        self.play_position = 0.0
        self.resume_at = 0.0
        self.last_tick = time.monotonic()

    def slider_changed(self, value):
        self.play_position = float(value)
        self.controller.apply(self.play_position)

    def set_autoplay(self, enabled):
        self.autoplay = bool(enabled)
        self.last_tick = time.monotonic()

    def drag_started(self, _widget, _event):
        self.dragging = True

    def drag_ended(self, _widget, _event):
        self.dragging = False
        self.resume_at = time.monotonic() + AUTOPLAY_RESUME_DELAY_S
        self.last_tick = time.monotonic()

    def on_timer(self, _step):
        now = time.monotonic()
        elapsed = max(0.0, now - self.last_tick)
        self.last_tick = now
        if self.dragging or not self.autoplay or now < self.resume_at or elapsed == 0.0:
            return
        if elapsed > AUTOPLAY_INTERVAL_S:
            return
        self.play_position += elapsed / AUTOPLAY_INTERVAL_S
        count = len(self.controller.weather.dates)
        if self.play_position >= count:
            self.play_position %= count
        visible_position = min(self.play_position, count - 1)
        self.controller.apply(visible_position)
        self.widget.GetRepresentation().SetValue(visible_position)


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
        fmt="%0.2f",
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
