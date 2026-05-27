"""Tool surface exposed to the model, and the dispatcher that runs them.

Each physical verb is a *dedicated* tool (not a generic "run_command"), so
the harness can gate hard-to-reverse actions, validate inputs at the
boundary, and log every motor command with typed arguments. The schemas
below are the exact JSON the Anthropic API expects in `tools`.
"""

from __future__ import annotations

from typing import Any, Callable

from ..bench import BenchController
from ..geometry import Vec3

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "scan_table",
        "description": (
            "Capture an overhead image and run part detection. Returns every "
            "part currently on the bench with its label, 3D position in "
            "millimetres (robot frame), and detector confidence. Call this "
            "first, and again whenever the table may have changed."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "pick_part",
        "description": (
            "Pick up a part by its label. The arm locates it via the latest "
            "scan, approaches from above, and grasps. Fails if the gripper is "
            "already holding something or the part is not found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Part label, e.g. 'resistor_330'."}
            },
            "required": ["label"],
            "additionalProperties": False,
        },
    },
    {
        "name": "place_part",
        "description": (
            "Place the currently-held part at a target position on the bench, "
            "in millimetres (robot frame). Use coordinates from scan_table to "
            "position parts relative to each other."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x_mm": {"type": "number"},
                "y_mm": {"type": "number"},
            },
            "required": ["x_mm", "y_mm"],
            "additionalProperties": False,
        },
    },
    {
        "name": "solder_joint",
        "description": (
            "Switch to the soldering iron and make a solder joint at the given "
            "position in millimetres. Use only on through-hole leads that are "
            "already seated."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x_mm": {"type": "number"},
                "y_mm": {"type": "number"},
            },
            "required": ["x_mm", "y_mm"],
            "additionalProperties": False,
        },
    },
    {
        "name": "park_arm",
        "description": "Move the arm to its home position, clear of the workspace.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "finish_assembly",
        "description": (
            "Declare the assembly complete. Provide a short summary of what was "
            "built. Call this only when every required step is done."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
            "additionalProperties": False,
        },
    },
]


class ToolDispatcher:
    """Maps a tool name + input to an action on the bench, returns a string."""

    def __init__(self, bench: BenchController):
        self.bench = bench
        self.done = False
        self.final_summary = ""
        self._handlers: dict[str, Callable[[dict[str, Any]], str]] = {
            "scan_table": self._scan_table,
            "pick_part": self._pick_part,
            "place_part": self._place_part,
            "solder_joint": self._solder_joint,
            "park_arm": self._park_arm,
            "finish_assembly": self._finish_assembly,
        }

    def dispatch(self, name: str, tool_input: dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if handler is None:
            return f"error: unknown tool '{name}'"
        return handler(tool_input)

    def _scan_table(self, _: dict[str, Any]) -> str:
        parts = self.bench.scan_table()
        if not parts:
            return "table is empty"
        held = self.bench.held_label()
        lines = [
            f"- {p.label}: x={p.world.x:.0f}mm y={p.world.y:.0f}mm "
            f"(conf {p.confidence:.2f})"
            for p in parts
        ]
        header = f"holding: {held}\n" if held else ""
        return header + "detected parts:\n" + "\n".join(lines)

    def _pick_part(self, tool_input: dict[str, Any]) -> str:
        label = tool_input["label"]
        part = self.bench.find(label)
        if part is None:
            return f"error: part '{label}' not found on the table"
        result = self.bench.skills.pick(part.world)
        return ("ok: " if result.ok else "error: ") + result.detail

    def _place_part(self, tool_input: dict[str, Any]) -> str:
        if self.bench.held_label() is None:
            return "error: gripper is empty -- pick a part before placing"
        point = Vec3(float(tool_input["x_mm"]), float(tool_input["y_mm"]), 0.0)
        result = self.bench.skills.place(point)
        return ("ok: " if result.ok else "error: ") + result.detail

    def _solder_joint(self, tool_input: dict[str, Any]) -> str:
        point = Vec3(float(tool_input["x_mm"]), float(tool_input["y_mm"]), 0.0)
        result = self.bench.skills.solder(point)
        return ("ok: " if result.ok else "error: ") + result.detail

    def _park_arm(self, _: dict[str, Any]) -> str:
        return "ok: " + self.bench.skills.park().detail

    def _finish_assembly(self, tool_input: dict[str, Any]) -> str:
        self.done = True
        self.final_summary = tool_input.get("summary", "")
        return "assembly marked complete"
