# `hk_weather` implementation package

All non-trivial project code will live in this package. The root scripts remain
small PEP 723 entry points so the assignment can still be run with commands such
as `uv run plot.py`.

Planned layers:

- `core/`: configuration, domain models and shared contracts.
- `pipeline/`: fetch, audit and preparation implementations.
- `data/`: local file readers and validation.
- `geometry/`: projection, terrain mesh, IDW and rainfall geometry.
- `render/`: reusable PyVista scene and visual layers.
- `interaction/`: timeline, camera limits, cursor probe and highlighting.
- `output/`: off-screen screenshot generation through the same scene builder.

The acquisition, audit and preparation implementations have moved into
`core/` and `pipeline/`; their root files are now thin entry points. The current
template renderer has also moved to `app.py` and will be replaced by the planned
PyVista renderer in the next implementation phase.
