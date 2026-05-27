"""High-level arm control: safe moves, and vacuum pick / place primitives.

The controller is the only thing that talks to the driver. It keeps track of
where the TCP is, raises every move to a safe travel height before crossing
the bench, and exposes the pick/place primitives the agent's tools call.
"""

from __future__ import annotations

from ..config import Config
from ..geometry import Pose
from ..safety import validate_pose
from .driver import ArmDriver, SimDriver
from .motion import plan_linear, solve_path


class ArmController:
    def __init__(self, config: Config | None = None, driver: ArmDriver | None = None):
        self.config = config or Config()
        self.driver = driver or SimDriver()
        self.current_pose: Pose | None = None
        self._started = False

    # ---- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        if self._started:
            return
        self.driver.connect()
        self.driver.home()
        self._started = True
        # Home leaves the TCP parked at the back of the bench, tool down.
        self.current_pose = Pose(
            x=self.config.work_area.x_min + 20.0,
            y=0.0,
            z=self.config.work_area.z_travel,
        )

    def stop(self) -> None:
        if not self._started:
            return
        self.driver.set_vacuum(False)
        self.driver.disconnect()
        self._started = False

    # ---- motion ------------------------------------------------------------
    def move_to(self, pose: Pose, speed_mm_s: float | None = None) -> Pose:
        """Move the TCP to ``pose`` in a straight line, validating every waypoint."""

        if not self._started:
            raise RuntimeError("controller not started; call start() first")
        speed = speed_mm_s if speed_mm_s is not None else self.config.move_speed_mm_s
        start = self.current_pose or pose
        for joints in solve_path(plan_linear(start, pose), self.config):
            self.driver.move_joints(joints, speed)
        self.current_pose = pose
        return pose

    def move_to_travel_height(self) -> None:
        if self.current_pose is None:
            return
        if self.current_pose.z < self.config.work_area.z_travel:
            self.move_to(self.current_pose.at_height(self.config.work_area.z_travel))

    def goto_xy(self, x: float, y: float, z: float, roll: float = 0.0) -> Pose:
        """Cross-bench move: lift to travel height, traverse, then descend."""

        target = Pose(x=x, y=y, z=z, tool_roll=roll)
        validate_pose(target, self.config)  # fail fast before moving
        self.move_to_travel_height()
        self.move_to(Pose(x=x, y=y, z=self.config.work_area.z_travel, tool_roll=roll))
        return self.move_to(target)

    # ---- end effector ------------------------------------------------------
    def pick_at(self, pose: Pose) -> None:
        """Vacuum-pick a part at ``pose`` (z = part top surface)."""

        approach = pose.above(self.config.approach_height)
        self.goto_xy(approach.x, approach.y, approach.z, roll=pose.tool_roll)
        self.move_to(pose.at_height(pose.z - self.config.pick_settle_z))
        self.driver.set_vacuum(True)
        self.move_to(approach)

    def place_at(self, pose: Pose) -> None:
        """Place the held part at ``pose`` (z = drop surface) and release vacuum."""

        approach = pose.above(self.config.approach_height)
        self.goto_xy(approach.x, approach.y, approach.z, roll=pose.tool_roll)
        self.move_to(pose)
        self.driver.set_vacuum(False)
        self.move_to(approach)

    def park(self) -> None:
        self.move_to_travel_height()
