"""Configuration: arm geometry, joint limits, and bench workspace bounds.

Defaults describe the reference TACTIN bench — a 5-DOF serial-bus servo arm
(Feetech STS3215 class, SO-ARM100 lineage) fitted with a vacuum pickup
nozzle, mounted at the back edge of a 600x400 mm work surface with an
overhead camera. Override via ``Config`` for a different arm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class JointLimit:
    lo: float  # radians
    hi: float  # radians

    def contains(self, value: float, tol: float = 1e-6) -> bool:
        return self.lo - tol <= value <= self.hi + tol


@dataclass(frozen=True)
class ArmSpec:
    """Link lengths (mm) and joint limits (rad) for the 5-DOF arm.

    The kinematic chain is: base yaw -> shoulder pitch -> elbow pitch ->
    wrist pitch -> wrist roll -> tool. ``base_height`` is the height of the
    shoulder axis above the bench; ``l3`` is the tool length from the wrist
    to the nozzle tip (TCP).
    """

    base_height: float = 120.0
    l1: float = 180.0  # shoulder -> elbow
    l2: float = 180.0  # elbow -> wrist
    l3: float = 80.0   # wrist -> nozzle tip (TCP)

    base_limit: JointLimit = JointLimit(-math.pi, math.pi)
    shoulder_limit: JointLimit = JointLimit(math.radians(-15), math.radians(195))
    elbow_limit: JointLimit = JointLimit(math.radians(-160), math.radians(160))
    wrist_limit: JointLimit = JointLimit(math.radians(-120), math.radians(120))
    roll_limit: JointLimit = JointLimit(-math.pi, math.pi)

    @property
    def max_reach(self) -> float:
        return self.l1 + self.l2 + self.l3

    def limits(self):
        return (
            self.base_limit,
            self.shoulder_limit,
            self.elbow_limit,
            self.wrist_limit,
            self.roll_limit,
        )


@dataclass(frozen=True)
class WorkArea:
    """Axis-aligned safe operating box for the TCP, in bench coordinates."""

    x_min: float = 70.0
    x_max: float = 300.0
    y_min: float = -150.0
    y_max: float = 150.0
    z_min: float = 0.0     # nozzle tip never drives below the bench surface
    z_max: float = 240.0
    z_travel: float = 140.0  # safe height for cross-bench moves

    def contains(self, x: float, y: float, z: float, tol: float = 1e-6) -> bool:
        return (
            self.x_min - tol <= x <= self.x_max + tol
            and self.y_min - tol <= y <= self.y_max + tol
            and self.z_min - tol <= z <= self.z_max + tol
        )


@dataclass(frozen=True)
class SerialConfig:
    port: str = "/dev/ttyUSB0"
    baud: int = 1_000_000
    timeout_s: float = 1.0


@dataclass(frozen=True)
class AgentConfig:
    model: str = "claude-opus-4-7"
    max_tokens: int = 8000
    effort: str = "high"
    max_steps: int = 40


@dataclass(frozen=True)
class Config:
    arm: ArmSpec = field(default_factory=ArmSpec)
    work_area: WorkArea = field(default_factory=WorkArea)
    serial: SerialConfig = field(default_factory=SerialConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    # Motion defaults
    approach_height: float = 25.0   # hover this far above a part before descending
    pick_settle_z: float = 0.5      # nozzle pressure offset at the part surface
    move_speed_mm_s: float = 120.0
