# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=2,<3"]
# ///

"""Validate the generated GitHub Pages artifact."""

from hk_weather.web.validate import validate_site


if __name__ == "__main__":
    validate_site()
