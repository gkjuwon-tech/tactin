"""Camera abstraction and a simulated overhead camera."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from ..sim import SimWorld


@dataclass
class Frame:
    """A captured image plus the time it was taken."""

    image: np.ndarray  # HxWx3 uint8
    timestamp: float
    width: int
    height: int


class Camera(ABC):
    """An overhead camera looking down at the bench."""

    @abstractmethod
    def capture(self) -> Frame:
        ...


class SimCamera(Camera):
    """Renders a top-down view of the simulated world.

    The render is intentionally simple (filled rectangles for part
    footprints). It exists so the rest of the pipeline has real pixels to
    work with; the SimDetector reads ground truth rather than these pixels.
    """

    def __init__(self, world: SimWorld, resolution: tuple[int, int] = (640, 480)):
        self.world = world
        self.width, self.height = resolution

    def _world_to_pixel(self, x_mm: float, y_mm: float) -> tuple[int, int]:
        tw, th = self.world.table_size_mm
        u = int(np.clip(x_mm / tw, 0, 1) * (self.width - 1))
        v = int(np.clip(y_mm / th, 0, 1) * (self.height - 1))
        return u, v

    def capture(self) -> Frame:
        img = np.full((self.height, self.width, 3), 30, dtype=np.uint8)
        for part in self.world.pickable_parts():
            u, v = self._world_to_pixel(part.position.x, part.position.y)
            fw, fh = part.footprint_mm
            tw, th = self.world.table_size_mm
            half_u = max(2, int(fw / tw * self.width / 2))
            half_v = max(2, int(fh / th * self.height / 2))
            color = _label_color(part.label)
            u0, u1 = max(0, u - half_u), min(self.width, u + half_u)
            v0, v1 = max(0, v - half_v), min(self.height, v + half_v)
            img[v0:v1, u0:u1] = color
        return Frame(img, time.time(), self.width, self.height)


def _label_color(label: str) -> tuple[int, int, int]:
    h = abs(hash(label))
    return (60 + h % 180, 60 + (h // 7) % 180, 60 + (h // 13) % 180)
