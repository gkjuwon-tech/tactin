import math

from tactin.geometry import Pose, Transform, Vec3


def test_vec3_distance():
    assert Vec3(0, 0, 0).distance_to(Vec3(3, 4, 0)) == 5.0


def test_pose_defaults_point_down():
    assert Pose().pitch == math.pi


def test_pose_offset_and_with_z():
    p = Pose(Vec3(10, 20, 30)).offset(dx=5, dz=-10).with_z(2)
    assert (p.position.x, p.position.y, p.position.z) == (15, 20, 2)


def test_transform_translation_roundtrip():
    t = Transform.from_translation(Vec3(1, 2, 3))
    moved = t.apply(Vec3(10, 10, 10))
    assert (moved.x, moved.y, moved.z) == (11, 12, 13)
    back = t.inverse().apply(moved)
    assert back.distance_to(Vec3(10, 10, 10)) < 1e-9
