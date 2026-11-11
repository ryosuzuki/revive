# Pipeline smoke test

This is an infrastructure acceptance test for the Revive implementation pipeline.
It is not a research-paper reconstruction, paper result, or device demonstration.
All test coordinates are synthetic. No external data, assets, network access,
third-party packages, Unity, GPU, or physical device is required.

## Usage

Run with Python 3.8 or newer, from this folder:

```python
from ray_box import ray_box_distance

distance = ray_box_distance(
    origin=(-2, 0.5, 0.5),
    direction=(2, 0, 0),
    bounds_min=(0, 0, 0),
    bounds_max=(1, 1, 1),
)
assert distance == 2.0
```

The function returns the nearest nonnegative **Euclidean distance** along the
forward ray, or `None` if it misses. Directions are normalized internally, so
the result is independent of their magnitude. For the parameterization
`origin + t * direction`, the corresponding parameter is
`t = distance / length(direction)`.

The box includes its boundary. An origin inside or on the box returns `0.0`;
tangencies and zero-width boxes count as intersections. Parallel rays miss if
their origin is outside the corresponding slab. Negative directions work on
every axis. A zero direction is rejected even for an inside origin.

Each input must be an iterable of exactly three finite real numbers representable
as Python floats; booleans and numeric strings are rejected. Malformed vectors,
NaN, infinity, zero directions, and bounds with a minimum greater than its maximum
raise `ValueError`. Equal bounds are valid.

The implementation intersects the three axis intervals using the slab method.
It uses constant time and space for three dimensions and the standard library
only. Float arithmetic has rounding limits: extreme coordinate differences or
distances can overflow to infinity, and extreme component ratios can underflow.
This utility does not provide arbitrary-precision or exact geometric predicates.

## Reproduce validation

There is no compilation or dependency installation step. Check source compilation
and run the regression suite from this folder:

```sh
python3 -m py_compile ray_box.py tests/test_ray_box.py
python3 -m unittest discover -s tests -v
```

Tests cover nearest hits, misses, parallel and negative directions, inside and
boundary origins, tangencies, degenerate boxes, invalid inputs, and translation
and direction-scale invariance. Explicit regressions check rays tangent to all six
faces in both travel directions, with nearby outside rays as miss controls. They
also reject NaN and positive/negative infinity in every component of every input,
including inputs that could otherwise trigger an early inside or miss result.
`REVIVE_RESULT.json` records the execution result. Its commands run from this folder.
There are no large deliverables or external artifacts.
