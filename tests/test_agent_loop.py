"""Exercise the tool-use loop with a scripted fake client (no network)."""

from __future__ import annotations

from dataclasses import dataclass, field

from tactin.arm.controller import ArmController
from tactin.arm.driver import SimDriver
from tactin.config import Config
from tactin.agent.runner import VibeSession
from tactin.workspace import Bench, Part


@dataclass
class Block:
    type: str
    text: str | None = None
    name: str | None = None
    input: dict | None = None
    id: str | None = None


@dataclass
class Response:
    content: list
    stop_reason: str


@dataclass
class FakeMessages:
    scripted: list
    calls: list = field(default_factory=list)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.scripted.pop(0)


class FakeClient:
    def __init__(self, scripted):
        self.messages = FakeMessages(scripted)


def make_session(scripted):
    cfg = Config()
    bench = Bench()
    bench.add_part(Part("led1", "led", x=130, y=-90, label="red 5mm"))
    arm = ArmController(cfg, SimDriver())
    return VibeSession(cfg, bench, arm, client=FakeClient(scripted)), bench, arm


def test_loop_executes_pick_and_place_then_finishes():
    scripted = [
        Response([Block("tool_use", name="list_parts", input={}, id="t1")], "tool_use"),
        Response([Block("tool_use", name="pick_part", input={"part_id": "led1"}, id="t2")],
                 "tool_use"),
        Response([Block("tool_use", name="place_part",
                        input={"x": 180, "y": 0, "z": 6}, id="t3")], "tool_use"),
        Response([Block("text", text="Done — placed the LED on the breadboard.")], "end_turn"),
    ]
    session, bench, arm = make_session(scripted)
    result = session.run("put the LED on the breadboard at 180,0")

    assert "Done" in result.final_text
    assert result.steps == 4
    names = [name for name, _ in result.tool_calls]
    assert names == ["list_parts", "pick_part", "place_part"]
    assert bench.get_part("led1").placed
    assert "vacuum on" in arm.driver.transcript
    assert "vacuum off" in arm.driver.transcript


def test_loop_feeds_errors_back_to_model():
    scripted = [
        Response([Block("tool_use", name="pick_part",
                        input={"part_id": "ghost"}, id="t1")], "tool_use"),
        Response([Block("text", text="No such part; stopping.")], "end_turn"),
    ]
    session, _bench, _arm = make_session(scripted)
    result = session.run("pick a part that does not exist")

    # The error tool_result was appended as a user turn for the model to read.
    tool_results = [m for m in session.messages if m["role"] == "user"][-1]["content"]
    assert tool_results[0]["is_error"] is True
    assert "error" in tool_results[0]["content"]
    assert "No such part" in result.final_text


def test_first_request_sends_cacheable_system_prefix():
    scripted = [Response([Block("text", text="nothing to do")], "end_turn")]
    session, _bench, _arm = make_session(scripted)
    session.run("idle")
    first_call = session.client.messages.calls[0]
    assert first_call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert first_call["model"] == "claude-opus-4-7"
    assert any(t["name"] == "pick_part" for t in first_call["tools"])
