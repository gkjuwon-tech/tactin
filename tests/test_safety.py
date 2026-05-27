import pytest

from tactin.config import Config
from tactin.geometry import Pose
from tactin.safety import SafetyError, validate_pose

CFG = Config()


def test_valid_pose_resolves_to_joints():
    joints = validate_pose(Pose(x=180.0, y=0.0, z=30.0), CFG)
    assert joints is not None


def test_pose_outside_work_area_rejected():
    # Beyond x_max
    with pytest.raises(SafetyError):
        validate_pose(Pose(x=10_000.0, y=0.0, z=30.0), CFG)


def test_pose_below_bench_surface_rejected():
    with pytest.raises(SafetyError):
        validate_pose(Pose(x=180.0, y=0.0, z=-5.0), CFG)


def test_unreachable_within_box_rejected():
    # Inside the work-area box but too far for the arm to reach: shrink the arm.
    from dataclasses import replace

    tiny = replace(CFG, arm=replace(CFG.arm, l1=40.0, l2=40.0, l3=20.0))
    with pytest.raises(SafetyError):
        validate_pose(Pose(x=300.0, y=150.0, z=200.0), tiny)
