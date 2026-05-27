"""Overhead camera capture.

The agent reasons about the bench from the overhead image directly (Claude
vision), so the camera's job is just to hand back an encoded frame. ``cv2``
is imported lazily; ``MockCamera`` serves a fixed image for tests and dry
runs with no camera attached.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass


class Camera:
    def capture_png(self) -> bytes:
        """Return the current overhead frame as PNG bytes."""
        raise NotImplementedError

    def capture_base64(self) -> tuple[str, str]:
        """Return ``(media_type, base64_data)`` ready for the Messages API."""
        return ("image/png", base64.standard_b64encode(self.capture_png()).decode("ascii"))


@dataclass
class MockCamera(Camera):
    png_bytes: bytes = b""

    def capture_png(self) -> bytes:
        if not self.png_bytes:
            raise RuntimeError("MockCamera has no image loaded")
        return self.png_bytes


@dataclass
class RealCamera(Camera):
    index: int = 0
    _cap: object = None

    def _capture(self):  # pragma: no cover - hardware path
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "opencv-python is required for RealCamera; `pip install tactin[vision]`"
            ) from exc
        if self._cap is None:
            self._cap = cv2.VideoCapture(self.index)
        ok, frame = self._cap.read()
        if not ok:
            raise RuntimeError("failed to read frame from camera")
        ok, buf = cv2.imencode(".png", frame)
        if not ok:
            raise RuntimeError("failed to encode frame")
        return bytes(buf)

    def capture_png(self) -> bytes:  # pragma: no cover - hardware path
        return self._capture()


def make_camera(kind: str = "mock", **kwargs) -> Camera:
    if kind == "mock":
        return MockCamera(**kwargs)
    if kind == "real":
        return RealCamera(**kwargs)
    raise ValueError(f"unknown camera kind {kind!r} (expected 'mock' or 'real')")
