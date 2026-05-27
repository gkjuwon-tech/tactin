"""Reachability checks.

Full inverse kinematics is delegated to the arm's own controller (every
desktop arm ships one). What the bench needs to guarantee is that a target
pose is inside the safe working volume before commanding a move, so we model
the workspace as a cylindrical shell plus a vertical range.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..geometry import Vec3


@dataclass(frozen=True)
class Workspace:
    """Safe operating volume relative to the arm base at the origin."""

    reach_min_mm: float = 60.0
    reach_max_mm: float = 320.0
    z_min_mm: float = -10.0
    z_max_mm: float = 250.0

    def contains(self, point: Vec3) -> bool:
        radius = math.hypot(point.x, point.y)
        return (
            self.reach_min_mm <= radius <= self.reach_max_mm
            and self.z_min_mm <= point.z <= self.z_max_mm
        )

    def clamp_reason(self, point: Vec3) -> str | None:
        """Return a human-readable reason a point is unreachable, else None."""
        radius = math.hypot(point.x, point.y)
        if radius < self.reach_min_mm:
            return f"too close to base ({radius:.0f}mm < {self.reach_min_mm:.0f}mm)"
        if radius > self.reach_max_mm:
            return f"out of reach ({radius:.0f}mm > {self.reach_max_mm:.0f}mm)"
        if point.z < self.z_min_mm:
            return f"below table ({point.z:.0f}mm < {self.z_min_mm:.0f}mm)"
        if point.z > self.z_max_mm:
            return f"too high ({point.z:.0f}mm > {self.z_max_mm:.0f}mm)"
        return None
