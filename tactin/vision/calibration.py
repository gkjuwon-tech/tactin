"""Camera-to-bench calibration.

Four ArUco markers at known bench coordinates define a planar homography from
image pixels to bench millimetres. With the camera looking straight down at a
flat bench this is exact; parts are assumed to sit on the bench plane, so a
single homography localizes every pixel the detector reports.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..geometry import apply_homography, compute_homography


@dataclass
class BenchCalibration:
    homography: list[list[float]]

    @classmethod
    def from_markers(
        cls,
        pixel_corners: list[tuple[float, float]],
        bench_corners: list[tuple[float, float]],
    ) -> "BenchCalibration":
        """Build calibration from 4 marker centres in pixels and their bench (x, y) mm."""

        return cls(homography=compute_homography(pixel_corners, bench_corners))

    def pixel_to_bench(self, px: float, py: float) -> tuple[float, float]:
        return apply_homography(self.homography, (px, py))
