"""Forward and inverse kinematics for the 5-DOF TACTIN arm.

The arm reduces to a base yaw plus a planar 3-link chain (shoulder, elbow,
wrist) acting in the vertical plane that contains the target, with a final
roll about the tool axis. This gives a closed-form IK that round-trips
exactly against the FK — see ``tests/test_kinematics.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .config import ArmSpec
from .geometry import Pose


class UnreachableError(ValueError):
    """Raised when a target pose lies outside the arm's reachable set."""


@dataclass(frozen=True)
class JointState:
    base: float      # q0: yaw about +Z
    shoulder: float  # q1: pitch from horizontal radial axis
    elbow: float     # q2: pitch relative to upper arm
    wrist: float     # q3: pitch relative to forearm
    roll: float      # q4: roll about the tool axis

    def as_tuple(self) -> tuple[float, float, float, float, float]:
        return (self.base, self.shoulder, self.elbow, self.wrist, self.roll)


def forward_kinematics(joints: JointState, spec: ArmSpec) -> Pose:
    """Map joint angles to the TCP pose in bench coordinates."""

    q0, q1, q2, _q3, q4 = joints.as_tuple()
    theta2 = q1 + q2                  # absolute angle of forearm
    theta3 = q1 + q2 + _q3            # absolute angle of tool

    elbow_r = spec.l1 * math.cos(q1)
    elbow_z = spec.base_height + spec.l1 * math.sin(q1)
    wrist_r = elbow_r + spec.l2 * math.cos(theta2)
    wrist_z = elbow_z + spec.l2 * math.sin(theta2)
    tcp_r = wrist_r + spec.l3 * math.cos(theta3)
    tcp_z = wrist_z + spec.l3 * math.sin(theta3)

    return Pose(
        x=tcp_r * math.cos(q0),
        y=tcp_r * math.sin(q0),
        z=tcp_z,
        tool_pitch=theta3,
        tool_roll=q4,
    )


def inverse_kinematics(pose: Pose, spec: ArmSpec, elbow_up: bool = True) -> JointState:
    """Solve joint angles for a TCP pose. Raises ``UnreachableError`` if out of reach."""

    q0 = math.atan2(pose.y, pose.x)
    radius = math.hypot(pose.x, pose.y)
    theta3 = pose.tool_pitch

    # Wrist centre: step back from the TCP along the tool axis by l3.
    wrist_r = radius - spec.l3 * math.cos(theta3)
    wrist_z = pose.z - spec.l3 * math.sin(theta3)

    dr = wrist_r
    dz = wrist_z - spec.base_height
    reach = math.hypot(dr, dz)

    if reach > spec.l1 + spec.l2 + 1e-6:
        raise UnreachableError(
            f"target too far: wrist distance {reach:.1f}mm > arm span "
            f"{spec.l1 + spec.l2:.1f}mm"
        )
    if reach < abs(spec.l1 - spec.l2) - 1e-6:
        raise UnreachableError(f"target too close to fold the arm: {reach:.1f}mm")

    beta = math.atan2(dz, dr)
    cos_alpha = (reach * reach + spec.l1 * spec.l1 - spec.l2 * spec.l2) / (
        2.0 * reach * spec.l1
    )
    alpha = math.acos(max(-1.0, min(1.0, cos_alpha)))

    q1 = beta + alpha if elbow_up else beta - alpha
    elbow_r = spec.l1 * math.cos(q1)
    elbow_z = spec.base_height + spec.l1 * math.sin(q1)
    theta2 = math.atan2(wrist_z - elbow_z, wrist_r - elbow_r)
    q2 = theta2 - q1
    q3 = theta3 - theta2

    return JointState(base=q0, shoulder=q1, elbow=q2, wrist=q3, roll=pose.tool_roll)


def joints_within_limits(joints: JointState, spec: ArmSpec) -> bool:
    return all(limit.contains(value) for value, limit in zip(joints.as_tuple(), spec.limits()))


def reachable(pose: Pose, spec: ArmSpec) -> bool:
    try:
        joints = inverse_kinematics(pose, spec)
    except UnreachableError:
        return False
    return joints_within_limits(joints, spec)
