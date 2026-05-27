"""Cartesian motion planning.

Straight-line moves are broken into small steps and each waypoint is solved
to joints, so the nozzle follows a predictable path instead of whatever arc
joint-space interpolation would produce. Every waypoint passes through the
safety gate, so an unreachable mid-path point fails the whole move up front.
"""

from __future__ import annotations

import math

from ..config import Config
from ..geometry import Pose, lerp
from ..kinematics import JointState
from ..safety import validate_pose


def plan_linear(start: Pose, end: Pose, step_mm: float = 8.0) -> list[Pose]:
    """Interpolate a straight TCP path from ``start`` to ``end`` (inclusive)."""

    span = math.dist(start.as_xyz(), end.as_xyz())
    steps = max(1, math.ceil(span / step_mm))
    path = []
    for i in range(1, steps + 1):
        t = i / steps
        path.append(
            Pose(
                x=lerp(start.x, end.x, t),
                y=lerp(start.y, end.y, t),
                z=lerp(start.z, end.z, t),
                tool_pitch=lerp(start.tool_pitch, end.tool_pitch, t),
                tool_roll=lerp(start.tool_roll, end.tool_roll, t),
            )
        )
    return path


def solve_path(path: list[Pose], config: Config) -> list[JointState]:
    """Resolve a list of poses to joint states, validating each against safety."""

    return [validate_pose(pose, config) for pose in path]
