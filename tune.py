# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=2,<3",
#   "pyproj>=3.7,<4",
# ]
# ///

"""Select fixed interpolation settings with leave-one-station-out validation."""

from hk_weather.pipeline.tune import main


if __name__ == "__main__":
    main()
