# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=2,<3",
#   "Pillow>=11,<13",
#   "pyproj>=3.7,<4",
#   "pyvista>=0.49,<0.50",
#   "shapely>=2,<3",
#   "vtk>=9.5,<10",
# ]
# ///

"""Generate browser-ready static data from the canonical Python pipeline."""

from hk_weather.app import load_project
from hk_weather.web.export import export_web_data


if __name__ == "__main__":
    weather, prepared = load_project()
    export_web_data(weather, prepared)
