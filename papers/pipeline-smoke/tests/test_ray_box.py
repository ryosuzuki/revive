"""Synthetic coordinates only; no external data or dependencies."""

import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ray_box import ray_box_distance


class RayBoxTests(unittest.TestCase):
    def cast(self, origin, direction, lo=(0, 0, 0), hi=(1, 1, 1)):
        return ray_box_distance(origin, direction, lo, hi)

    def test_nearest_hit(self):
        self.assertEqual(self.cast((-2, 0.5, 0.5), (1, 0, 0)), 2.0)

    def test_diagonal_distance(self):
        self.assertAlmostEqual(self.cast((-1, -1, -1), (1, 1, 1)), math.sqrt(3))

    def test_miss_disjoint_slab_intervals(self):
        self.assertIsNone(self.cast((-2, -4, 0.5), (1, 1, 0)))

    def test_box_behind_ray(self):
        self.assertIsNone(self.cast((2, 0.5, 0.5), (1, 0, 0)))

    def test_parallel_outside_each_axis(self):
        for axis in range(3):
            for outside in (-1, 2):
                origin = [0.5, 0.5, 0.5]
                direction = [0, 0, 0]
                origin[axis] = outside
                direction[(axis + 1) % 3] = 1
                with self.subTest(axis=axis, outside=outside):
                    self.assertIsNone(self.cast(origin, direction))

    def test_parallel_on_boundary(self):
        self.assertEqual(self.cast((-2, 0, 1), (1, 0, -0.0)), 2)

    def test_tangent_to_each_face(self):
        # Travel through the interior of a face, avoiding edges and corners.
        for normal_axis in range(3):
            travel_axis = (normal_axis + 1) % 3
            for face in (0, 1):
                for sign in (-1, 1):
                    origin = [0.5, 0.5, 0.5]
                    direction = [0, 0, 0]
                    origin[normal_axis] = face
                    origin[travel_axis] = -2 if sign == 1 else 3
                    direction[travel_axis] = sign * 2
                    with self.subTest(axis=normal_axis, face=face, sign=sign):
                        self.assertEqual(self.cast(origin, direction), 2.0)
                        # Moving just outside that face must turn it into a miss.
                        origin[normal_axis] = -0.001 if face == 0 else 1.001
                        self.assertIsNone(self.cast(origin, direction))

    def test_inside(self):
        self.assertEqual(self.cast((0.5, 0.5, 0.5), (1, -2, 3)), 0.0)

    def test_boundary_pointing_outward(self):
        self.assertEqual(self.cast((0, 0.5, 0.5), (-1, 0, 0)), 0.0)

    def test_negative_direction_each_axis(self):
        for axis in range(3):
            origin = [0.5, 0.5, 0.5]
            direction = [0, 0, 0]
            origin[axis] = 4
            direction[axis] = -2
            with self.subTest(axis=axis):
                self.assertEqual(self.cast(origin, direction), 3)

    def test_tangent_corner(self):
        self.assertAlmostEqual(self.cast((-1, 1, 0.5), (1, -1, 0)), math.sqrt(2))

    def test_degenerate_point_box(self):
        self.assertAlmostEqual(self.cast((-1, -1, -1), (1, 1, 1), (0, 0, 0), (0, 0, 0)), math.sqrt(3))
        self.assertIsNone(self.cast((-1, 1, 0), (1, 0, 0), (0, 0, 0), (0, 0, 0)))

    def test_zero_direction_rejected_inside_and_outside(self):
        for origin in ((0.5, 0.5, 0.5), (-2, 0, 0)):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                self.cast(origin, (0, -0.0, 0))

    def test_inverted_bounds_each_axis(self):
        for axis in range(3):
            lo = [0, 0, 0]
            lo[axis] = 2
            with self.subTest(axis=axis), self.assertRaises(ValueError):
                self.cast((0, 0, 0), (1, 0, 0), lo)

    def test_malformed_vectors_all_arguments(self):
        invalid = [None, (), (0, 0), (0, 0, 0, 0), "abc", (0, "1", 0),
                   (False, 0, 0), (complex(1, 1), 0, 0), (10 ** 1000, 0, 0)]
        invalid += [(value, 0, 0) for value in (math.nan, math.inf, -math.inf)]
        for index in range(4):
            for value in invalid:
                args = [(-1, 0.5, 0.5), (1, 0, 0), (0, 0, 0), (1, 1, 1)]
                args[index] = value
                with self.subTest(argument=index, value=value), self.assertRaises(ValueError):
                    ray_box_distance(*args)

    def test_direction_scale_invariance(self):
        for scale in (1e-300, 0.1, 1, 7, 1e300):
            with self.subTest(scale=scale):
                self.assertAlmostEqual(self.cast((-1, -1, -1), (scale,) * 3), math.sqrt(3))

    def test_nonfinite_rejected_in_every_argument_and_component(self):
        for argument in range(4):
            for axis in range(3):
                for value in (math.nan, math.inf, -math.inf):
                    args = [[-1, 0.5, 0.5], [1, 0, 0], [0, 0, 0], [1, 1, 1]]
                    args[argument][axis] = value
                    with self.subTest(argument=argument, axis=axis, value=value):
                        with self.assertRaises(ValueError):
                            ray_box_distance(*args)

    def test_nonfinite_rejected_before_inside_or_miss_shortcuts(self):
        for origin in ((0.5, 0.5, 0.5), (2, 0.5, 0.5)):
            for value in (math.nan, math.inf, -math.inf):
                with self.subTest(origin=origin, value=value):
                    with self.assertRaises(ValueError):
                        self.cast(origin, (0, 1, 0), hi=(1, 1, value))

    def test_small_nonzero_component_is_not_parallel(self):
        self.assertEqual(self.cast((-1, 0.5, 0.5), (1e-300, 0, 0)), 1)

    def test_translation_invariance(self):
        for offset in (-100, 0, 200):
            shift = lambda vector: tuple(x + offset for x in vector)
            with self.subTest(offset=offset):
                self.assertAlmostEqual(self.cast(shift((-1, -1, -1)), (1, 1, 1),
                                                 shift((0, 0, 0)), shift((1, 1, 1))), math.sqrt(3))

    def test_iterable_inputs(self):
        self.assertEqual(self.cast(iter((-2, 0.5, 0.5)), [2, 0, 0]), 2)


if __name__ == "__main__":
    unittest.main()
