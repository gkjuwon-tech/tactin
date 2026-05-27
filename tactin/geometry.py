"""Pure-Python geometry: poses, small linear algebra, planar homography.

All distances are millimetres, all angles radians, unless noted. The bench
frame has its origin at the robot arm base, +X pointing away from the
operator, +Y to the left, +Z up.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

# Tool pointing straight down (-Z) corresponds to a tool-pitch angle of -90°
# measured from the horizontal radial axis in the arm plane.
TOOL_DOWN = -math.pi / 2


@dataclass(frozen=True)
class Pose:
    """A target pose for the tool centre point (TCP).

    ``tool_pitch`` is the angle of the tool axis from horizontal in the
    vertical plane that contains the target; ``TOOL_DOWN`` means the nozzle
    points straight down, which is what top-down pick-and-place wants.
    ``tool_roll`` rotates the part about the tool axis (used to orient ICs,
    headers, etc.).
    """

    x: float
    y: float
    z: float
    tool_pitch: float = TOOL_DOWN
    tool_roll: float = 0.0

    def at_height(self, z: float) -> "Pose":
        return replace(self, z=z)

    def above(self, dz: float) -> "Pose":
        return replace(self, z=self.z + dz)

    def as_xyz(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve A x = b by Gaussian elimination with partial pivoting.

    Operates on a copy; raises ValueError when the system is singular.
    """

    n = len(matrix)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("singular matrix")
        a[col], a[pivot] = a[pivot], a[col]
        pivot_val = a[col][col]
        for r in range(n):
            if r == col:
                continue
            factor = a[r][col] / pivot_val
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                a[r][c] -= factor * a[col][c]
    return [a[i][n] / a[i][i] for i in range(n)]


def compute_homography(
    src: list[tuple[float, float]], dst: list[tuple[float, float]]
) -> list[list[float]]:
    """Compute the 3x3 homography mapping ``src`` pixels to ``dst`` points.

    Needs exactly four point correspondences (the bench's four ArUco corner
    markers). The bottom-right element is fixed to 1, leaving eight unknowns.
    """

    if len(src) != 4 or len(dst) != 4:
        raise ValueError("homography needs exactly 4 point correspondences")
    rows: list[list[float]] = []
    rhs: list[float] = []
    for (sx, sy), (dx, dy) in zip(src, dst):
        rows.append([sx, sy, 1, 0, 0, 0, -dx * sx, -dx * sy])
        rhs.append(dx)
        rows.append([0, 0, 0, sx, sy, 1, -dy * sx, -dy * sy])
        rhs.append(dy)
    h = solve_linear(rows, rhs)
    return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]]


def apply_homography(h: list[list[float]], point: tuple[float, float]) -> tuple[float, float]:
    px, py = point
    w = h[2][0] * px + h[2][1] * py + h[2][2]
    if abs(w) < 1e-12:
        raise ValueError("degenerate homography mapping")
    x = (h[0][0] * px + h[0][1] * py + h[0][2]) / w
    y = (h[1][0] * px + h[1][1] * py + h[1][2]) / w
    return (x, y)
