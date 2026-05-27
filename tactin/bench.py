"""The bench controller: wires the layers into one object.

This is the integration seam. The CLI and the agent both talk to a
`BenchController` rather than reaching into vision/robot/sim directly, so
swapping the simulator for real hardware is a one-line change here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import Vec3
from .robot import MotionSkills, SimRobotArm, Workspace
from .sim import SimWorld, example_blinky_world
from .vision import HandEyeCalibration, SimCamera, SimDetector


@dataclass
class DetectedPart:
    label: str
    world: Vec3
    confidence: float


class BenchController:
    """Everything needed to perceive the table and move the arm."""

    def __init__(self, world: SimWorld | None = None, camera_res: tuple[int, int] = (640, 480)):
        self.world = world or example_blinky_world()
        self.camera = SimCamera(self.world, resolution=camera_res)
        self.detector = SimDetector(self.world, self.camera)
        self.calibration = HandEyeCalibration(
            image_size=camera_res,
            table_size_mm=self.world.table_size_mm,
            table_height_mm=self.world.table_height_mm,
        )
        self.arm = SimRobotArm(self.world)
        self.skills = MotionSkills(self.arm, Workspace(reach_max_mm=600.0))

    def scan_table(self) -> list[DetectedPart]:
        frame = self.camera.capture()
        detections = self.detector.detect(frame)
        out: list[DetectedPart] = []
        for d in detections:
            world = self.calibration.pixel_to_world(*d.center_px)
            out.append(DetectedPart(d.label, world, d.confidence))
        return out

    def find(self, label: str) -> DetectedPart | None:
        for part in self.scan_table():
            if part.label == label:
                return part
        return None

    def held_label(self) -> str | None:
        return self.world.held_part.label if self.world.held_part else None
