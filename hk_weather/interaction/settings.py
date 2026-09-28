"""Collapsible screen-space settings for the desktop viewer."""


class SettingsPanel:
    def __init__(self, plotter, timeline):
        self.plotter = plotter
        self.timeline = timeline
        height = plotter.window_size[1]
        self.autoplay_label = plotter.add_text(
            "AUTOPLAY",
            position=(70, height - 179),
            font_size=11,
            color="#dcecef",
            shadow=True,
        )
        self.autoplay_widget = plotter.add_checkbox_button_widget(
            self.timeline.set_autoplay,
            value=True,
            position=(30, height - 195),
            size=26,
            border_size=3,
            color_on="#ffe36b",
            color_off="#42545a",
            background_color="#07151b",
        )
        self.toggle_label = plotter.add_text(
            "SETTINGS",
            position=(70, height - 127),
            font_size=11,
            color="#dcecef",
            shadow=True,
        )
        self.toggle_widget = plotter.add_checkbox_button_widget(
            self.set_visible,
            value=False,
            position=(30, height - 143),
            size=26,
            border_size=3,
            color_on="#9bc8d2",
            color_off="#42545a",
            background_color="#07151b",
        )
        self.set_visible(False)

    def set_visible(self, visible):
        """Keep the settings tab visible while toggling its contents."""
        self.autoplay_widget.SetEnabled(bool(visible))
        self.autoplay_label.SetVisibility(bool(visible))
        self.plotter.render()
