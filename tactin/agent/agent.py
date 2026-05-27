"""The assembly agent.

`AssemblyAgent` drives the bench through a manual tool-use loop against the
Claude API. We use the manual loop (not the SDK tool runner) on purpose:
these tools move a physical arm, so the harness wants a seam to log, gate, or
require human approval before each motor command.

When no API key is present the agent falls back to a deterministic greedy
planner so the whole stack still runs offline -- the demo never needs the
network. The planner is intentionally simple (pick each BOM part, place it on
the breadboard); it is the floor, the LLM loop is the ceiling.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from ..bench import BenchController
from ..planning import BOM
from .tools import TOOL_SPECS, ToolDispatcher

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """\
You are TacTin, the controller for a robot-arm assembly bench used by hardware \
engineers to prototype circuits. A developer has placed loose components on the \
bench and given you an assembly task.

Your job: drive the arm to build what was asked, using the tools provided.

Operating rules:
- Always scan_table before you reason about positions; never assume a part is \
where you last saw it.
- Plan the order of operations before acting. Place large carrier parts \
(breadboard, dev board) first, then smaller components onto them.
- Coordinates are millimetres in the robot frame, taken from scan results.
- The gripper holds one part at a time. Pick, place, then pick the next.
- Only solder leads that are already seated through-hole.
- When every required component is placed (and soldered, if asked), call \
finish_assembly with a short summary. Do not keep working after that.
Think step by step, but keep tool calls purposeful -- each one moves a motor.\
"""


@dataclass
class AgentResult:
    completed: bool
    summary: str
    transcript: list[str] = field(default_factory=list)
    used_llm: bool = False


class AssemblyAgent:
    def __init__(self, bench: BenchController, max_steps: int = 40):
        self.bench = bench
        self.max_steps = max_steps

    def run(self, task: str, bom: BOM | None = None) -> AgentResult:
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                return self._run_llm(task, bom)
            except Exception as exc:  # noqa: BLE001 - fall back, but surface why
                fallback = self._run_offline(task, bom)
                fallback.transcript.insert(0, f"[llm unavailable: {exc}; using offline planner]")
                return fallback
        return self._run_offline(task, bom)

    # -- LLM-driven loop ---------------------------------------------------
    def _run_llm(self, task: str, bom: BOM | None) -> AgentResult:
        import anthropic

        client = anthropic.Anthropic()
        dispatcher = ToolDispatcher(self.bench)
        transcript: list[str] = []

        user_text = task if bom is None else f"{task}\n\nBill of materials:\n" + _format_bom(bom)
        messages: list[dict] = [{"role": "user", "content": user_text}]

        system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]

        for _ in range(self.max_steps):
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                thinking={"type": "adaptive"},
                system=system,
                tools=TOOL_SPECS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    transcript.append(f"[think] {block.text.strip()}")

            if response.stop_reason != "tool_use" or not tool_uses:
                break

            results = []
            for tu in tool_uses:
                output = dispatcher.dispatch(tu.name, tu.input)
                transcript.append(f"[tool] {tu.name}({tu.input}) -> {output}")
                results.append(
                    {"type": "tool_result", "tool_use_id": tu.id, "content": output}
                )
            messages.append({"role": "user", "content": results})

            if dispatcher.done:
                break

        return AgentResult(
            completed=dispatcher.done,
            summary=dispatcher.final_summary or "stopped without finishing",
            transcript=transcript,
            used_llm=True,
        )

    # -- Offline deterministic planner -------------------------------------
    def _run_offline(self, task: str, bom: BOM | None) -> AgentResult:
        dispatcher = ToolDispatcher(self.bench)
        transcript: list[str] = []

        def step(name: str, **kwargs) -> str:
            out = dispatcher.dispatch(name, kwargs)
            transcript.append(f"[tool] {name}({kwargs}) -> {out}")
            return out

        step("scan_table")
        parts = self.bench.scan_table()
        labels = [p.label for p in parts]

        # Place carriers first, then everything else onto a grid near them.
        carriers = [l for l in ("breadboard", "esp32_devkit") if l in labels]
        components = [l for l in labels if l not in carriers]

        base = self.bench.find(carriers[0]) if carriers else None
        bx = base.world.x if base else 200.0
        by = base.world.y if base else 150.0

        order = carriers + components
        for i, label in enumerate(order):
            if step("pick_part", label=label).startswith("error"):
                continue
            tx = bx + (i % 5) * 12.0 - 24.0
            ty = by + (i // 5) * 12.0
            step("place_part", x_mm=tx, y_mm=ty)

        step("park_arm")
        placed = [l for l in order]
        step("finish_assembly", summary=f"placed {len(placed)} parts: {', '.join(placed)}")

        return AgentResult(
            completed=dispatcher.done,
            summary=dispatcher.final_summary,
            transcript=transcript,
            used_llm=False,
        )


def _format_bom(bom: BOM) -> str:
    return "\n".join(
        f"- {p.ref} {p.label} {p.value} [{p.package}] x{p.qty}".rstrip()
        for p in bom.parts
    )
