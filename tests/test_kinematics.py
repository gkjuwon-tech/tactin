import math

import pytest

from tactin.config import ArmSpec
from tactin.geometry import Pose, TOOL_DOWN
from tactin.kinematics import (
    UnreachableError,
    forward_kinematics,
    inverse_kinematics,
    joints_within_limits,
)

SPEC = ArmSpec()


def test_ik_fk_round_trip_top_down():
    pose = Pose(x=200.0, y=40.0, z=30.0)
    joints = inverse_kinematics(pose, SPEC)
    back = forward_kinematics(joints, SPEC)
    assert math.dist(pose.as_xyz(), back.as_xyz()) < 1e-6
    assert abs(back.tool_pitch - TOOL_DOWN) < 1e-6


def test_ik_fk_round_trip_across_workspace():
    worst = 0.0
    for x in range(90, 291, 25):
        for y in range(-150, 151, 50):
            for z in (15, 45, 90):
                pose = Pose(x=float(x), y=float(y), z=float(z))
                try:
                    joints = inverse_kinematics(pose, SPEC)
                except UnreachableError:
                    continue
                back = forward_kinematics(joints, SPEC)
                worst = max(worst, math.dist(pose.as_xyz(), back.as_xyz()))
    assert worst < 1e-6


def test_tool_roll_is_preserved():
    pose = Pose(x=180.0, y=0.0, z=20.0, tool_roll=0.5)
    joints = inverse_kinematics(pose, SPEC)
    assert abs(joints.roll - 0.5) < 1e-9
    assert abs(forward_kinematics(joints, SPEC).tool_roll - 0.5) < 1e-9


def test_unreachable_far_target_raises():
    with pytest.raises(UnreachableError):
        inverse_kinematics(Pose(x=2000.0, y=0.0, z=20.0), SPEC)


def test_base_yaw_points_at_target():
    joints = inverse_kinematics(Pose(x=0.0, y=150.0, z=30.0), SPEC)
    assert abs(joints.base - math.pi / 2) < 1e-9


def test_home_pose_within_limits():
    # A mid-workspace pose should resolve to in-limit joints.
    joints = inverse_kinematics(Pose(x=180.0, y=0.0, z=40.0), SPEC)
    assert joints_within_limits(joints, SPEC)
