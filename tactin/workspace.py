"""The bench world model.

Tracks what the arm believes is on the workbench: parts (with their bench
coordinates), part trays, and named placement targets such as a breadboard.
Vision populates and refreshes this model; the agent reads it to plan and
mutates it as it picks and places.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .geometry import Pose


@dataclass
class Part:
    """A component sitting on the bench (or held by the nozzle)."""

    id: str
    kind: str                  # "resistor", "led", "ic", "header", "wire", "capacitor", ...
    x: float
    y: float
    z: float = 2.0             # top surface height; the nozzle picks at this z
    label: str = ""            # value/marking, e.g. "330Ω", "ESP32", "1uF"
    rotation: float = 0.0      # part yaw on the bench (rad)
    held: bool = False
    placed: bool = False

    def pick_pose(self) -> Pose:
        return Pose(x=self.x, y=self.y, z=self.z, tool_roll=self.rotation)


@dataclass
class Slot:
    """A named place to put a part — a breadboard hole row, a tray cell, etc."""

    name: str
    x: float
    y: float
    z: float = 6.0
    occupied_by: str | None = None


@dataclass
class Bench:
    parts: dict[str, Part] = field(default_factory=dict)
    slots: dict[str, Slot] = field(default_factory=dict)

    # ---- parts -------------------------------------------------------------
    def add_part(self, part: Part) -> Part:
        self.parts[part.id] = part
        return part

    def get_part(self, part_id: str) -> Part:
        if part_id not in self.parts:
            raise KeyError(f"unknown part {part_id!r}")
        return self.parts[part_id]

    def available_parts(self) -> list[Part]:
        return [p for p in self.parts.values() if not p.held and not p.placed]

    def find(self, kind: str | None = None, label: str | None = None) -> list[Part]:
        results = []
        for part in self.available_parts():
            if kind is not None and part.kind != kind:
                continue
            if label is not None and label.lower() not in part.label.lower():
                continue
            results.append(part)
        return results

    def held_part(self) -> Part | None:
        for part in self.parts.values():
            if part.held:
                return part
        return None

    # ---- slots -------------------------------------------------------------
    def add_slot(self, slot: Slot) -> Slot:
        self.slots[slot.name] = slot
        return slot

    def get_slot(self, name: str) -> Slot:
        if name not in self.slots:
            raise KeyError(f"unknown slot {name!r}")
        return self.slots[name]

    # ---- mutations ---------------------------------------------------------
    def mark_picked(self, part_id: str) -> Part:
        if self.held_part() is not None:
            raise RuntimeError("nozzle already holds a part; place it before picking another")
        part = self.get_part(part_id)
        if part.placed:
            raise RuntimeError(f"part {part_id!r} was already placed")
        part.held = True
        return part

    def mark_placed(self, x: float, y: float, z: float, slot: str | None = None) -> Part:
        part = self.held_part()
        if part is None:
            raise RuntimeError("nothing is held; cannot place")
        part.held = False
        part.placed = True
        part.x, part.y, part.z = x, y, z
        if slot is not None:
            self.get_slot(slot).occupied_by = part.id
        return part

    def summary(self) -> str:
        lines = []
        held = self.held_part()
        lines.append(f"held: {held.id + ' (' + held.label + ')' if held else 'nothing'}")
        avail = self.available_parts()
        lines.append(f"parts on bench ({len(avail)}):")
        for part in avail:
            mark = f" [{part.label}]" if part.label else ""
            lines.append(f"  - {part.id}: {part.kind}{mark} at ({part.x:.0f}, {part.y:.0f})")
        if self.slots:
            lines.append("slots:")
            for slot in self.slots.values():
                state = f"occupied by {slot.occupied_by}" if slot.occupied_by else "free"
                lines.append(f"  - {slot.name} at ({slot.x:.0f}, {slot.y:.0f}) — {state}")
        return "\n".join(lines)
