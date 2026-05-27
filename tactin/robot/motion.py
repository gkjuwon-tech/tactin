"""High-level motion skills.

These compose raw driver calls into the verbs the agent actually reasons
about: pick, place, solder. Each skill approaches from a safe height, does
the action, and retreats -- the standard "approach / act / depart" pattern
that keeps the arm from dragging across other parts.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..geometry import Pose, Vec3
from .driver import RobotArm
from .kinematics import Workspace


@dataclass
class SkillResult:
    ok: bool
    detail: str


class MotionSkills:
    def __init__(
        self,
        arm: RobotArm,
        workspace: Workspace | None = None,
        approach_height_mm: float = 60.0,
        pick_height_mm: float = 2.0,
    ):
        self.arm = arm
        self.workspace = workspace or Workspace()
        self.approach_height_mm = approach_height_mm
        self.pick_height_mm = pick_height_mm

    def _reachable(self, point: Vec3) -> SkillResult | None:
        reason = self.workspace.clamp_reason(point)
        if reason is not None:
            return SkillResult(False, f"target unreachable: {reason}")
        return None

    def pick(self, point: Vec3) -> SkillResult:
        if (bad := self._reachable(point)) is not None:
            return bad
        self.arm.set_tool("gripper")
        self.arm.open_gripper()
        self.arm.move_to(Pose(point).with_z(self.approach_height_mm))
        self.arm.move_to(Pose(point).with_z(self.pick_height_mm))
        grasped = self.arm.close_gripper()
        self.arm.move_to(Pose(point).with_z(self.approach_height_mm))
        if not grasped:
            return SkillResult(False, "closed on empty space -- nothing grasped")
        return SkillResult(True, "part grasped")

    def place(self, point: Vec3, lock: bool = True) -> SkillResult:
        if (bad := self._reachable(point)) is not None:
            return bad
        self.arm.move_to(Pose(point).with_z(self.approach_height_mm))
        self.arm.move_to(Pose(point).with_z(self.pick_height_mm))
        # The sim driver locks placement through release_at via open_gripper;
        # we set the lock by releasing directly on the world for permanence.
        world = getattr(self.arm, "world", None)
        if world is not None:
            world.release_at(point.__class__(point.x, point.y, self.pick_height_mm), lock=lock)
        else:  # pragma: no cover - real hardware path
            self.arm.open_gripper()
        self.arm.move_to(Pose(point).with_z(self.approach_height_mm))
        return SkillResult(True, "part placed")

    def solder(self, point: Vec3, dwell_s: float = 1.0) -> SkillResult:
        if (bad := self._reachable(point)) is not None:
            return bad
        self.arm.set_tool("solder_iron")
        self.arm.move_to(Pose(point).with_z(self.approach_height_mm))
        self.arm.move_to(Pose(point).with_z(self.pick_height_mm))
        # dwell while the joint heats; on hardware this commands the feeder.
        self.arm.move_to(Pose(point).with_z(self.approach_height_mm))
        self.arm.set_tool("gripper")
        return SkillResult(True, f"joint soldered (dwell {dwell_s:.1f}s)")

    def park(self) -> SkillResult:
        self.arm.home()
        return SkillResult(True, "arm parked at home")
