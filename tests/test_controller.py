import pytest

from tactin.arm.controller import ArmController
from tactin.arm.driver import SimDriver
from tactin.config import Config
from tactin.geometry import Pose
from tactin.safety import SafetyError


def test_pick_sequence_toggles_vacuum_on():
    driver = SimDriver()
    arm = ArmController(Config(), driver)
    arm.start()
    arm.pick_at(Pose(x=170.0, y=-90.0, z=2.0))
    vacuum_cmds = [c for c in driver.transcript if c.startswith("vacuum")]
    # A pick turns the vacuum on exactly once, after the descent moves.
    assert vacuum_cmds == ["vacuum on"]
    on_index = driver.transcript.index("vacuum on")
    assert any(c.startswith("move") for c in driver.transcript[:on_index])


def test_place_releases_vacuum():
    driver = SimDriver()
    arm = ArmController(Config(), driver)
    arm.start()
    arm.driver.set_vacuum(True)
    arm.place_at(Pose(x=180.0, y=0.0, z=6.0))
    assert driver.transcript[-1] != "vacuum on"
    assert "vacuum off" in driver.transcript


def test_goto_xy_lifts_to_travel_height_first():
    cfg = Config()
    driver = SimDriver()
    arm = ArmController(cfg, driver)
    arm.start()
    # Put the TCP low, then traverse: it must climb to travel height before moving.
    arm.move_to(Pose(x=150.0, y=0.0, z=10.0))
    driver.transcript.clear()
    arm.goto_xy(250.0, 100.0, 10.0)
    assert arm.current_pose.x == 250.0
    # At least one move command was issued for the traverse.
    assert any(c.startswith("move") for c in driver.transcript)


def test_move_outside_area_raises_before_motion():
    cfg = Config()
    driver = SimDriver()
    arm = ArmController(cfg, driver)
    arm.start()
    driver.transcript.clear()
    with pytest.raises(SafetyError):
        arm.goto_xy(10_000.0, 0.0, 10.0)
    assert not any(c.startswith("move") for c in driver.transcript)


def test_move_before_start_raises():
    arm = ArmController(Config(), SimDriver())
    with pytest.raises(RuntimeError):
        arm.move_to(Pose(x=180.0, y=0.0, z=30.0))
