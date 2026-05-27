"""Safety envelope checks.

Every motion target is validated here before it reaches the driver: it must
sit inside the work-area box, be kinematically reachable, and respect joint
limits. This is the one gate that protects the bench, the parts, and the arm.
"""

from __future__ import annotations

from .config import Config
from .geometry import Pose
from .kinematics import JointState, UnreachableError, inverse_kinematics, joints_within_limits


class SafetyError(RuntimeError):
    """Raised when a requested motion would violate the safety envelope."""


def validate_pose(pose: Pose, config: Config) -> JointState:
    """Validate and resolve a TCP pose to joint angles, or raise ``SafetyError``."""

    area = config.work_area
    if not area.contains(pose.x, pose.y, pose.z):
        raise SafetyError(
            f"pose ({pose.x:.0f}, {pose.y:.0f}, {pose.z:.0f}) is outside the work area "
            f"[x {area.x_min:.0f}..{area.x_max:.0f}, y {area.y_min:.0f}..{area.y_max:.0f}, "
            f"z {area.z_min:.0f}..{area.z_max:.0f}]"
        )
    try:
        joints = inverse_kinematics(pose, config.arm)
    except UnreachableError as exc:
        raise SafetyError(str(exc)) from exc
    if not joints_within_limits(joints, config.arm):
        raise SafetyError("pose requires a joint angle beyond its mechanical limit")
    return joints
