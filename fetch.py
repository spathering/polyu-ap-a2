# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.32,<3"]
# ///

"""Fetch and cache the project's raw source data once."""

from hk_weather.pipeline.fetch import main


if __name__ == "__main__":
    main()
