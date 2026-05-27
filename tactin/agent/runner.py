"""The agentic loop: instruction in, assembled prototype out.

A manual tool-use loop (so we keep full control over safety gating and step
limits). On each turn it sends the frozen system prompt + tool schemas (a
stable, cached prefix) plus the running conversation, executes whatever tools
the model asks for, and feeds the results back until the model stops calling
tools. The Anthropic client is injected, so the loop is exercised in tests
with a scripted fake client and no network.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..arm.controller import ArmController
from ..config import Config
from ..vision.camera import Camera
from ..workspace import Bench
from .prompts import system_blocks
from .tools import TOOLS, ToolBox


@dataclass
class RunResult:
    final_text: str
    steps: int
    tool_calls: list[tuple[str, dict]] = field(default_factory=list)


def _text_of(content) -> str:
    parts = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


class VibeSession:
    def __init__(
        self,
        config: Config,
        bench: Bench,
        controller: ArmController,
        camera: Camera | None = None,
        client: object | None = None,
    ):
        self.config = config
        self.bench = bench
        self.controller = controller
        self.camera = camera
        self.toolbox = ToolBox(bench, controller, config)
        self._client = client
        self.messages: list[dict] = []

    @property
    def client(self):
        if self._client is None:
            import anthropic  # lazy: only needed for a live run

            self._client = anthropic.Anthropic()
        return self._client

    def _initial_user_content(self, instruction: str) -> list[dict]:
        content: list[dict] = []
        if self.camera is not None:
            media_type, data = self.camera.capture_base64()
            content.append(
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                }
            )
        content.append(
            {
                "type": "text",
                "text": (
                    f"Bench state:\n{self.bench.summary()}\n\n"
                    f"Task: {instruction}"
                ),
            }
        )
        return content

    def run(self, instruction: str) -> RunResult:
        self.controller.start()
        self.messages = [{"role": "user", "content": self._initial_user_content(instruction)}]
        tool_calls: list[tuple[str, dict]] = []

        for step in range(1, self.config.agent.max_steps + 1):
            response = self.client.messages.create(
                model=self.config.agent.model,
                max_tokens=self.config.agent.max_tokens,
                system=system_blocks(),
                tools=TOOLS,
                messages=self.messages,
                thinking={"type": "adaptive"},
                output_config={"effort": self.config.agent.effort},
            )
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return RunResult(_text_of(response.content), step, tool_calls)

            results = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                tool_calls.append((block.name, dict(block.input)))
                text, is_error = self.toolbox.dispatch(block.name, dict(block.input))
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": text,
                        "is_error": is_error,
                    }
                )
            self.messages.append({"role": "user", "content": results})

        return RunResult(
            f"stopped after reaching the {self.config.agent.max_steps}-step limit",
            self.config.agent.max_steps,
            tool_calls,
        )
