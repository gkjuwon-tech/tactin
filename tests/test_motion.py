from tactin.geometry import Vec3
from tactin.robot import MotionSkills, SimRobotArm, Workspace
from tactin.sim import SimPart, SimWorld


def _world_with_part(at: Vec3) -> SimWorld:
    w = SimWorld()
    w.add_part(SimPart("widget", at))
    return w


def test_pick_then_place_moves_the_part():
    world = _world_with_part(Vec3(150, 100, 0))
    skills = MotionSkills(SimRobotArm(world), Workspace(reach_max_mm=600))

    assert skills.pick(Vec3(150, 100, 0)).ok
    assert world.held_part is not None and world.held_part.label == "widget"

    assert skills.place(Vec3(200, 120, 0)).ok
    assert world.held_part is None
    part = world.parts[0]
    assert part.placed is True
    assert (round(part.position.x), round(part.position.y)) == (200, 120)


def test_pick_empty_space_fails_cleanly():
    world = _world_with_part(Vec3(150, 100, 0))
    skills = MotionSkills(SimRobotArm(world), Workspace(reach_max_mm=600))
    result = skills.pick(Vec3(10, 10, 0))  # nothing within tolerance + unreachable
    assert not result.ok


def test_unreachable_target_is_rejected():
    world = _world_with_part(Vec3(150, 100, 0))
    skills = MotionSkills(SimRobotArm(world), Workspace(reach_max_mm=200))
    result = skills.pick(Vec3(500, 500, 0))
    assert not result.ok
    assert "unreachable" in result.detail
