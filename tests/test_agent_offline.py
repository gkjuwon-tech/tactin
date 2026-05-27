from tactin.agent import AssemblyAgent
from tactin.bench import BenchController


def test_offline_agent_completes_blinky(monkeypatch):
    # Force the offline planner regardless of environment.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    bench = BenchController()
    result = AssemblyAgent(bench).run("place all the parts on the breadboard")

    assert result.completed
    assert result.used_llm is False
    # every detected part should have ended up placed (locked) on the table
    assert all(p.placed for p in bench.world.parts)
