"""Dependency-free intersections of forward 3D rays and closed axis-aligned boxes."""

import math
from numbers import Real


def _vector(value, name):
    try:
        components = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must contain three finite real numbers") from exc
    if len(components) != 3:
        raise ValueError(f"{name} must contain exactly three components")
    result = []
    for component in components:
        if isinstance(component, bool) or not isinstance(component, Real):
            raise ValueError(f"{name} must contain finite real numbers")
        try:
            number = float(component)
        except (OverflowError, ValueError) as exc:
            raise ValueError(f"{name} components must fit finite floats") from exc
        if not math.isfinite(number):
            raise ValueError(f"{name} must contain finite real numbers")
        result.append(number)
    return tuple(result)


def ray_box_distance(origin, direction, bounds_min, bounds_max):
    """Return the nearest nonnegative Euclidean distance, or None for a miss.

    All arguments are iterables of three finite real numbers. The box is closed
    and may have zero extent on any axis. Direction need not be unit length.
    An origin in or on the box returns 0.0. A zero direction, inverted bounds,
    or malformed vector raises ValueError, even when the origin is inside.

    Uses the slab method with exact zero checks for parallel components, without
    an epsilon that could incorrectly classify a small direction as parallel.
    Computation uses Python floating-point arithmetic.
    """
    origin = _vector(origin, "origin")
    direction = _vector(direction, "direction")
    lower = _vector(bounds_min, "bounds_min")
    upper = _vector(bounds_max, "bounds_max")
    if any(lo > hi for lo, hi in zip(lower, upper)):
        raise ValueError("bounds_min must be <= bounds_max on every axis")

    # Scale first so normalization handles both tiny and very large directions.
    scale = max(abs(component) for component in direction)
    if scale == 0.0:
        raise ValueError("direction must be nonzero")
    scaled = tuple(component / scale for component in direction)
    length = math.hypot(*scaled)
    unit = tuple(component / length for component in scaled)

    entry, exit_distance = 0.0, math.inf
    for position, velocity, lo, hi in zip(origin, unit, lower, upper):
        if velocity == 0.0:
            if position < lo or position > hi:
                return None
            continue
        first = (lo - position) / velocity
        second = (hi - position) / velocity
        near, far = min(first, second), max(first, second)
        entry = max(entry, near)
        exit_distance = min(exit_distance, far)
        if entry > exit_distance:
            return None
    return entry
