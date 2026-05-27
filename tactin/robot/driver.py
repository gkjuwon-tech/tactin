"""Robot arm driver abstraction.

`RobotArm` is the seam between the bench software and physical hardware.
Implement it for a Dobot / xArm / myCobot / UR and everything above keeps
working. `SimRobotArm` implements it against the SimWorld so the full stack
runs headless.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from ..geometry import Pose, Vec3
from ..sim import SimWorld

log = logging.getLogger("tactin.robot")


class RobotArm(ABC):
    @abstractmethod
    def home(self) -> None:
        ...

    @abstractmethod
    def move_to(self, pose: Pose, speed: float = 1.0) -> None:
        ...

    @abstractmethod
    def get_pose(self) -> Pose:
        ...

    @abstractmethod
    def open_gripper(self) -> None:
        ...

    @abstractmethod
    def close_gripper(self) -> bool:
        """Close the gripper. Returns True if something was grasped."""
        ...

    @abstractmethod
    def set_tool(self, tool: str) -> None:
        """Select an end effector, e.g. 'gripper' or 'solder_iron'."""
        ...


class SimRobotArm(RobotArm):
    """Simulated arm. Moves are instantaneous; grasps act on the SimWorld."""

    HOME = Pose(Vec3(0, 150, 200))

    def __init__(self, world: SimWorld, grasp_tolerance_mm: float = 6.0):
        self.world = world
        self.grasp_tolerance_mm = grasp_tolerance_mm
        self._pose = self.HOME
        self.tool = "gripper"
        self.move_count = 0

    def home(self) -> None:
        self.move_to(self.HOME)

    def move_to(self, pose: Pose, speed: float = 1.0) -> None:
        self._pose = pose
        self.move_count += 1
        p = pose.position
        log.debug("move_to (%.0f, %.0f, %.0f) tool=%s", p.x, p.y, p.z, self.tool)

    def get_pose(self) -> Pose:
        return self._pose

    def open_gripper(self) -> None:
        self.world.release_at(self._pose.position, lock=False)

    def close_gripper(self) -> bool:
        part = self.world.grab(self._pose.position, self.grasp_tolerance_mm)
        return part is not None

    def set_tool(self, tool: str) -> None:
        if self.world.held_part is not None:
            raise RuntimeError("cannot change tool while holding a part")
        self.tool = tool
