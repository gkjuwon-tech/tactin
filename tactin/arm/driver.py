"""Drivers that turn joint commands into servo motion.

``SimDriver`` is the default: it records every command so the rest of the
stack (and the tests) can run with no hardware attached. ``SerialDriver``
speaks the line protocol implemented by the ESP32 firmware in
``firmware/tactin_arm_esp32`` over USB; pyserial is imported lazily so it is
only required when you actually drive a real arm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..config import SerialConfig
from ..kinematics import JointState


class ArmDriver:
    """Interface every driver implements. Angles are radians."""

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def home(self) -> None: ...

    def move_joints(self, joints: JointState, speed_mm_s: float) -> None: ...

    def set_vacuum(self, on: bool) -> None: ...


@dataclass
class SimDriver(ArmDriver):
    """A no-hardware driver that records the command transcript."""

    transcript: list[str] = field(default_factory=list)
    connected: bool = False
    vacuum_on: bool = False
    last_joints: JointState | None = None

    def connect(self) -> None:
        self.connected = True
        self.transcript.append("connect")

    def disconnect(self) -> None:
        self.connected = False
        self.transcript.append("disconnect")

    def home(self) -> None:
        self.transcript.append("home")
        self.last_joints = JointState(0.0, math.pi / 2, 0.0, -math.pi / 2, 0.0)

    def move_joints(self, joints: JointState, speed_mm_s: float) -> None:
        if not self.connected:
            raise RuntimeError("driver not connected")
        self.last_joints = joints
        degs = " ".join(f"{math.degrees(a):.1f}" for a in joints.as_tuple())
        self.transcript.append(f"move {degs} @ {speed_mm_s:.0f}")

    def set_vacuum(self, on: bool) -> None:
        self.vacuum_on = on
        self.transcript.append(f"vacuum {'on' if on else 'off'}")


@dataclass
class SerialDriver(ArmDriver):
    """Drives the real arm over USB serial using the firmware line protocol.

    Protocol (newline-terminated ASCII):
      ``M b s e w r v``   move to joint angles in degrees, ``v`` = feedrate
      ``V 1`` / ``V 0``   vacuum solenoid on / off
      ``H``               home
    The firmware replies ``ok`` for each accepted command.
    """

    serial_config: SerialConfig = field(default_factory=SerialConfig)
    _port: object = field(default=None, repr=False)

    def connect(self) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:  # pragma: no cover - hardware path
            raise RuntimeError(
                "pyserial is required for SerialDriver; `pip install tactin[hardware]`"
            ) from exc
        self._port = serial.Serial(
            self.serial_config.port,
            self.serial_config.baud,
            timeout=self.serial_config.timeout_s,
        )

    def disconnect(self) -> None:  # pragma: no cover - hardware path
        if self._port is not None:
            self._port.close()
            self._port = None

    def _send(self, line: str) -> None:  # pragma: no cover - hardware path
        if self._port is None:
            raise RuntimeError("driver not connected")
        self._port.write((line + "\n").encode("ascii"))
        self._port.readline()  # consume the 'ok'

    def home(self) -> None:  # pragma: no cover - hardware path
        self._send("H")

    def move_joints(self, joints: JointState, speed_mm_s: float) -> None:  # pragma: no cover
        degs = " ".join(f"{math.degrees(a):.2f}" for a in joints.as_tuple())
        self._send(f"M {degs} {speed_mm_s:.0f}")

    def set_vacuum(self, on: bool) -> None:  # pragma: no cover - hardware path
        self._send(f"V {1 if on else 0}")


def make_driver(kind: str = "sim", serial_config: SerialConfig | None = None) -> ArmDriver:
    if kind == "sim":
        return SimDriver()
    if kind == "serial":
        return SerialDriver(serial_config=serial_config or SerialConfig())
    raise ValueError(f"unknown driver kind {kind!r} (expected 'sim' or 'serial')")
