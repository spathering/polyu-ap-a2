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

"""Render the project visualisation through the package application."""

from hk_weather.app import main


if __name__ == "__main__":
    main()
