"""Turn pixel detections into bench parts.

A detection is a part the vision stage found in the overhead image: its kind,
marking, pixel centre, and on-bench rotation. Detections can come from a
trained model or from Claude reading the overhead frame; either way they are
localized to bench coordinates through the calibration and loaded into the
``Bench`` model.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..workspace import Part
from .calibration import BenchCalibration


@dataclass
class Detection:
    kind: str
    px: float
    py: float
    label: str = ""
    rotation: float = 0.0
    confidence: float = 1.0


def detections_to_parts(
    detections: list[Detection],
    calibration: BenchCalibration,
    surface_z: float = 2.0,
    id_prefix: str = "p",
) -> list[Part]:
    parts: list[Part] = []
    for i, det in enumerate(detections):
        x, y = calibration.pixel_to_bench(det.px, det.py)
        parts.append(
            Part(
                id=f"{id_prefix}{i + 1}",
                kind=det.kind,
                x=x,
                y=y,
                z=surface_z,
                label=det.label,
                rotation=det.rotation,
            )
        )
    return parts
