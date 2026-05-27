import math

import pytest

from tactin.geometry import (
    apply_homography,
    clamp,
    compute_homography,
    solve_linear,
)


def test_solve_linear_simple():
    # 2x + y = 5 ; x - y = 1  ->  x = 2, y = 1
    sol = solve_linear([[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0])
    assert abs(sol[0] - 2.0) < 1e-9
    assert abs(sol[1] - 1.0) < 1e-9


def test_solve_linear_singular_raises():
    with pytest.raises(ValueError):
        solve_linear([[1.0, 1.0], [2.0, 2.0]], [1.0, 2.0])


def test_homography_identity_recovers_points():
    src = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    h = compute_homography(src, src)
    for p in src:
        out = apply_homography(h, p)
        assert math.dist(out, p) < 1e-6


def test_homography_maps_pixel_square_to_bench():
    # A 640x480 image whose corners map to a 260x360 mm bench rectangle.
    pixels = [(0.0, 0.0), (640.0, 0.0), (640.0, 480.0), (0.0, 480.0)]
    bench = [(60.0, 180.0), (320.0, 180.0), (320.0, -180.0), (60.0, -180.0)]
    h = compute_homography(pixels, bench)
    # Image centre maps to bench-rectangle centre.
    cx, cy = apply_homography(h, (320.0, 240.0))
    assert abs(cx - 190.0) < 1e-6
    assert abs(cy - 0.0) < 1e-6


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(99, 0, 10) == 10
