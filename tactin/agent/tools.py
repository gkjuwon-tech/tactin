"""Robot tools exposed to the LLM, and the dispatcher that executes them.

The schemas are deliberately small and typed — pick, place, move, look, and
register a placement target — so the model has a tight, unambiguous surface.
Every handler routes through the controller (which enforces the safety
envelope) and the bench model (which enforces the one-part-at-a-time rule),
so a hallucinated or unsafe call fails loudly instead of moving the arm.
"""

from __future__ import annotations

import math

from ..arm.controller import ArmController
from ..config import Config
from ..geometry import Pose
from ..safety import SafetyError
from ..workspace import Bench, Slot

TOOLS: list[dict] = [
    {
        "name": "list_parts",
        "description": (
            "List the parts currently on the bench (id, kind, marking, location), the "
            "part held by the nozzle if any, and registered placement slots. Call this "
            "first and whenever you need to re-check state."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "add_slot",
        "description": (
            "Register a named placement target at a bench coordinate, e.g. a breadboard "
            "hole position or an output tray cell, so you can place parts there by name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Unique slot name."},
                "x": {"type": "number", "description": "Bench X in mm."},
                "y": {"type": "number", "description": "Bench Y in mm."},
                "z": {"type": "number", "description": "Drop-surface Z in mm (default 6)."},
            },
            "required": ["name", "x", "y"],
            "additionalProperties": False,
        },
    },
    {
        "name": "pick_part",
        "description": (
            "Vacuum-pick the part with the given id. Fails if the nozzle already holds a "
            "part or if the part is unreachable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"part_id": {"type": "string"}},
            "required": ["part_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "place_part",
        "description": (
            "Place the held part. Give either a slot name, or explicit x/y(/z) bench "
            "coordinates. Optionally rotate the part about the vertical axis (degrees)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "slot": {"type": "string", "description": "Name of a registered slot."},
                "x": {"type": "number", "description": "Bench X in mm (if no slot)."},
                "y": {"type": "number", "description": "Bench Y in mm (if no slot)."},
                "z": {"type": "number", "description": "Drop-surface Z in mm (default 6)."},
                "rotation_deg": {"type": "number", "description": "Part rotation in degrees."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "move_to",
        "description": (
            "Diagnostic move of the empty nozzle to a bench coordinate, e.g. to point at "
            "a location. Does not pick or place."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number", "description": "Height in mm (default travel height)."},
            },
            "required": ["x", "y"],
            "additionalProperties": False,
        },
    },
]


class ToolBox:
    """Executes tool calls against a bench model and an arm controller."""

    def __init__(self, bench: Bench, controller: ArmController, config: Config | None = None):
        self.bench = bench
        self.controller = controller
        self.config = config or controller.config

    def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        """Run a tool call. Returns ``(result_text, is_error)``."""

        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            return (f"unknown tool {name!r}", True)
        try:
            return (handler(args), False)
        except (SafetyError, KeyError, RuntimeError, ValueError) as exc:
            return (f"error: {exc}", True)

    # ---- handlers ----------------------------------------------------------
    def _tool_list_parts(self, args: dict) -> str:
        return self.bench.summary()

    def _tool_add_slot(self, args: dict) -> str:
        slot = Slot(
            name=str(args["name"]),
            x=float(args["x"]),
            y=float(args["y"]),
            z=float(args.get("z", 6.0)),
        )
        self.bench.add_slot(slot)
        return f"registered slot {slot.name!r} at ({slot.x:.0f}, {slot.y:.0f}, {slot.z:.0f})"

    def _tool_pick_part(self, args: dict) -> str:
        part = self.bench.get_part(str(args["part_id"]))
        self.controller.pick_at(part.pick_pose())
        self.bench.mark_picked(part.id)
        return f"picked {part.id} ({part.kind} {part.label})".strip()

    def _tool_place_part(self, args: dict) -> str:
        held = self.bench.held_part()
        if held is None:
            raise RuntimeError("nothing is held; pick a part before placing")

        rotation = math.radians(float(args.get("rotation_deg", 0.0)))
        slot_name = args.get("slot")
        if slot_name is not None:
            slot = self.bench.get_slot(str(slot_name))
            x, y, z = slot.x, slot.y, slot.z
        else:
            if "x" not in args or "y" not in args:
                raise ValueError("place_part needs either a slot or x and y")
            x, y, z = float(args["x"]), float(args["y"]), float(args.get("z", 6.0))

        self.controller.place_at(Pose(x=x, y=y, z=z, tool_roll=rotation))
        self.bench.mark_placed(x, y, z, slot=str(slot_name) if slot_name else None)
        where = f"slot {slot_name!r}" if slot_name else f"({x:.0f}, {y:.0f}, {z:.0f})"
        return f"placed {held.id} at {where}"

    def _tool_move_to(self, args: dict) -> str:
        x, y = float(args["x"]), float(args["y"])
        z = float(args.get("z", self.config.work_area.z_travel))
        self.controller.goto_xy(x, y, z)
        return f"moved nozzle to ({x:.0f}, {y:.0f}, {z:.0f})"
