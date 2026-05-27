"""Camera <-> robot calibration.

Converts a pixel coordinate from the overhead camera into a 3D point in the
robot's coordinate frame. The bench assumes parts rest on a flat table at a
known height, so a 2D homography (pixel -> table plane) plus the table height
is enough to recover a full 3D pick point.
"""

from __future__ import annotations

from ..geometry import Vec3


class HandEyeCalibration:
    """Linear pixel->table-plane mapping for a fixed overhead camera.

    For a real bench this is solved from a calibration target (e.g. a
    ChArUco board) touched by the arm. Here we construct it directly from
    the known table size and image resolution, which is exactly the mapping
    the simulated camera uses -- so the loop closes.
    """

    def __init__(
        self,
        image_size: tuple[int, int],
        table_size_mm: tuple[float, float],
        table_height_mm: float = 0.0,
    ):
        self.width, self.height = image_size
        self.table_w, self.table_h = table_size_mm
        self.table_height_mm = table_height_mm

    def pixel_to_world(self, u: int, v: int) -> Vec3:
        x = u / max(1, self.width - 1) * self.table_w
        y = v / max(1, self.height - 1) * self.table_h
        return Vec3(x, y, self.table_height_mm)
