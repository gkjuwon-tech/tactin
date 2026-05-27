"""Part detection.

`PartDetector` is the interface a real vision model would implement (e.g. a
fine-tuned open-vocabulary detector returning labels + boxes + pose).
`SimDetector` fakes it by reading ground truth from the simulated world,
adding pixel noise so downstream code must cope with imperfect detections.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from ..sim import SimWorld
from .camera import Camera, Frame, SimCamera


@dataclass
class Detection:
    """One detected part in image space."""

    label: str
    center_px: tuple[int, int]
    bbox_px: tuple[int, int, int, int]  # x0, y0, x1, y1
    confidence: float


class PartDetector(ABC):
    @abstractmethod
    def detect(self, frame: Frame) -> list[Detection]:
        ...


class SimDetector(PartDetector):
    """Ground-truth detector for the simulator, with optional pixel noise."""

    def __init__(self, world: SimWorld, camera: SimCamera, noise_px: float = 1.5, seed: int = 0):
        self.world = world
        self.camera = camera
        self.noise_px = noise_px
        self._rng = np.random.default_rng(seed)

    def detect(self, frame: Frame) -> list[Detection]:
        detections: list[Detection] = []
        for part in self.world.pickable_parts():
            u, v = self.camera._world_to_pixel(part.position.x, part.position.y)
            du, dv = self._rng.normal(0, self.noise_px, size=2)
            cu, cv = int(u + du), int(v + dv)
            fw, fh = part.footprint_mm
            tw, th = self.world.table_size_mm
            half_u = max(2, int(fw / tw * self.camera.width / 2))
            half_v = max(2, int(fh / th * self.camera.height / 2))
            detections.append(
                Detection(
                    label=part.label,
                    center_px=(cu, cv),
                    bbox_px=(cu - half_u, cv - half_v, cu + half_u, cv + half_v),
                    confidence=float(self._rng.uniform(0.85, 0.99)),
                )
            )
        return detections


class ModelPartDetector(PartDetector):
    """Adapter for a real vision model. Left unimplemented on purpose.

    To go live, wrap your detector here -- run inference on `frame.image`
    and translate its output into `Detection` objects. The rest of the
    pipeline (calibration, motion, agent) is model-agnostic.
    """

    def __init__(self, model) -> None:  # pragma: no cover - integration point
        self.model = model

    def detect(self, frame: Frame) -> list[Detection]:  # pragma: no cover
        raise NotImplementedError(
            "Plug a trained detector in here and emit Detection objects."
        )
