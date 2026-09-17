# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Run the HKO source-data completeness audit."""

from hk_weather.pipeline.audit import main


if __name__ == "__main__":
    main()
