"""Spatial primitives shared across the stack.

Units are millimetres for position and radians for orientation, matching the
convention most desktop robot arms expose over their APIs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def as_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=float)

    def distance_to(self, other: "Vec3") -> float:
        return float(np.linalg.norm(self.as_array() - other.as_array()))

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    @staticmethod
    def from_array(a: np.ndarray) -> "Vec3":
        return Vec3(float(a[0]), float(a[1]), float(a[2]))


@dataclass(frozen=True)
class Pose:
    """A tool-tip pose: position plus roll/pitch/yaw orientation."""

    position: Vec3 = Vec3()
    roll: float = 0.0
    pitch: float = math.pi  # tool pointing straight down by default
    yaw: float = 0.0

    def with_z(self, z: float) -> "Pose":
        p = self.position
        return Pose(Vec3(p.x, p.y, z), self.roll, self.pitch, self.yaw)

    def offset(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "Pose":
        p = self.position
        return Pose(Vec3(p.x + dx, p.y + dy, p.z + dz), self.roll, self.pitch, self.yaw)

    def rotation_matrix(self) -> np.ndarray:
        return _rpy_to_matrix(self.roll, self.pitch, self.yaw)


def _rpy_to_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return rz @ ry @ rx


@dataclass(frozen=True)
class Transform:
    """A rigid 4x4 transform, used for camera<->robot calibration."""

    matrix: np.ndarray

    @staticmethod
    def identity() -> "Transform":
        return Transform(np.eye(4))

    @staticmethod
    def from_translation(t: Vec3) -> "Transform":
        m = np.eye(4)
        m[:3, 3] = t.as_array()
        return Transform(m)

    @staticmethod
    def from_rotation_translation(rpy: tuple[float, float, float], t: Vec3) -> "Transform":
        m = np.eye(4)
        m[:3, :3] = _rpy_to_matrix(*rpy)
        m[:3, 3] = t.as_array()
        return Transform(m)

    def apply(self, point: Vec3) -> Vec3:
        homog = np.append(point.as_array(), 1.0)
        return Vec3.from_array((self.matrix @ homog)[:3])

    def inverse(self) -> "Transform":
        return Transform(np.linalg.inv(self.matrix))

    def __matmul__(self, other: "Transform") -> "Transform":
        return Transform(self.matrix @ other.matrix)
