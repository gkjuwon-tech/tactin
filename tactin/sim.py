"""A minimal simulated physical world.

The simulator is the trick that makes the whole stack runnable with zero
hardware: the camera "sees" the parts that live here, and the robot arm's
pick/place actions mutate this same state. Swap the simulator for real
drivers and the layers above do not change.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .geometry import Vec3


@dataclass
class SimPart:
    """A physical part lying on (or held above) the table."""

    label: str  # e.g. "resistor_10k", "esp32_devkit"
    position: Vec3
    footprint_mm: tuple[float, float] = (5.0, 2.0)  # bounding box on the table
    held: bool = False
    placed: bool = False  # locked into the assembly, no longer pickable

    def clone(self) -> "SimPart":
        return copy.deepcopy(self)


@dataclass
class SimWorld:
    """Ground-truth state of the bench. Owns the parts and the gripper."""

    table_size_mm: tuple[float, float] = (400.0, 300.0)
    table_height_mm: float = 0.0
    parts: list[SimPart] = field(default_factory=list)
    held_part: SimPart | None = None
    gripper_open: bool = True

    def add_part(self, part: SimPart) -> None:
        self.parts.append(part)

    def pickable_parts(self) -> list[SimPart]:
        return [p for p in self.parts if not p.held and not p.placed]

    def nearest_part(self, point: Vec3, max_dist_mm: float) -> SimPart | None:
        candidates = [
            (p.position.distance_to(point), p) for p in self.pickable_parts()
        ]
        candidates = [(d, p) for d, p in candidates if d <= max_dist_mm]
        if not candidates:
            return None
        candidates.sort(key=lambda dp: dp[0])
        return candidates[0][1]

    def grab(self, point: Vec3, tolerance_mm: float = 6.0) -> SimPart | None:
        if self.held_part is not None:
            raise RuntimeError("gripper already holding a part")
        target = self.nearest_part(point, tolerance_mm)
        if target is None:
            return None
        target.held = True
        self.held_part = target
        self.gripper_open = False
        return target

    def release_at(self, point: Vec3, lock: bool = False) -> SimPart | None:
        if self.held_part is None:
            return None
        part = self.held_part
        part.position = point
        part.held = False
        part.placed = lock
        self.held_part = None
        self.gripper_open = True
        return part

    def snapshot(self) -> dict:
        return {
            "held": self.held_part.label if self.held_part else None,
            "gripper_open": self.gripper_open,
            "parts": [
                {
                    "label": p.label,
                    "pos": [p.position.x, p.position.y, p.position.z],
                    "placed": p.placed,
                }
                for p in self.parts
            ],
        }


def example_blinky_world() -> SimWorld:
    """A starter scene: parts for a classic 'blink an LED' breadboard build."""

    world = SimWorld()
    world.add_part(SimPart("esp32_devkit", Vec3(80, 200, 0), (55, 28)))
    world.add_part(SimPart("breadboard", Vec3(220, 150, 0), (165, 55)))
    world.add_part(SimPart("led_red", Vec3(120, 60, 0), (5, 5)))
    world.add_part(SimPart("resistor_330", Vec3(160, 50, 0), (6, 2)))
    world.add_part(SimPart("jumper_wire", Vec3(300, 70, 0), (60, 1)))
    return world
