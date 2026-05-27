"""Assembly plan model.

The agent emits a plan as an ordered list of steps; this module gives that
plan a typed shape and a couple of sanity checks. Keeping the plan as data
(not just a sequence of tool calls) lets us preview, validate, and log it
before any motor moves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Action = Literal["pick", "place", "solder", "inspect"]


@dataclass
class AssemblyStep:
    action: Action
    target_label: str  # which part / joint this step acts on
    note: str = ""


@dataclass
class AssemblyPlan:
    name: str
    steps: list[AssemblyStep] = field(default_factory=list)

    def validate(self, available_labels: list[str]) -> list[str]:
        """Return a list of problems; empty means the plan looks consistent."""
        problems: list[str] = []
        holding = False
        seen = set(available_labels)
        for i, step in enumerate(self.steps):
            if step.action == "pick":
                if holding:
                    problems.append(f"step {i}: pick while already holding a part")
                if step.target_label not in seen:
                    problems.append(f"step {i}: pick of unknown part '{step.target_label}'")
                holding = True
            elif step.action == "place":
                if not holding:
                    problems.append(f"step {i}: place with empty gripper")
                holding = False
        if holding:
            problems.append("plan ends while still holding a part")
        return problems
