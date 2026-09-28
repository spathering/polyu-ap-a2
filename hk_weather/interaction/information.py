"""Collapsible data-source and interpolation notes for the desktop viewer."""


INFORMATION = (
    "DATA & METHOD\n\n"
    "Hong Kong Observatory daily station data, April 2026\n"
    "Temperature: data.gov.hk daily mean temperature\n"
    "Rainfall: data.gov.hk daily total rainfall\n"
    "Locations: weather.gov.hk weather stations\n"
    "Land mask: official Hong Kong 18-district boundary\n\n"
    "HK total rainfall sums the 21 displayed station totals.\n"
    "HK mean temperature averages the same 21 stations.\n\n"
    "Temperature: exact k-nearest IDW (p=1.5, k=20).\n"
    "Rainfall: exact log1p local IDW (p=2.5, k=8).\n"
    "Parameters use leave-one-station-out validation.\n\n"
    "Only daily station values are observations. Values between\n"
    "stations and dates are estimates, not hourly measurements."
)


class InformationPanel:
    def __init__(self, plotter):
        self.plotter = plotter
        width, height = plotter.window_size
        self.text_actor = plotter.add_text(
            INFORMATION,
            position=(max(20, width - 520), max(120, height - 430)),
            font_size=10,
            color="#dcecef",
            shadow=True,
        )
        text_property = self.text_actor.GetTextProperty()
        text_property.SetBackgroundColor(0.025, 0.08, 0.105)
        text_property.SetBackgroundOpacity(0.84)
        self.toggle_label = plotter.add_text(
            "DATA & METHOD",
            position=(width - 195, height - 127),
            font_size=11,
            color="#dcecef",
            shadow=True,
        )
        self.toggle_widget = plotter.add_checkbox_button_widget(
            self.set_visible,
            value=False,
            position=(width - 235, height - 143),
            size=26,
            border_size=3,
            color_on="#9bc8d2",
            color_off="#42545a",
            background_color="#07151b",
        )
        self.set_visible(False)

    def set_visible(self, visible):
        self.text_actor.SetVisibility(bool(visible))
        self.plotter.render()
