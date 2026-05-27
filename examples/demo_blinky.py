"""Run the assembly agent on the blinky BOM, against the simulator.

    python examples/demo_blinky.py

With ANTHROPIC_API_KEY set, the Claude tool-calling loop drives the bench.
Without it, the deterministic offline planner runs the same tool surface so
the demo always works.
"""

from pathlib import Path

from tactin.agent import AssemblyAgent
from tactin.bench import BenchController
from tactin.planning import load_bom

BOM = Path(__file__).resolve().parents[1] / "bom" / "blinky.yaml"


def main() -> None:
    bench = BenchController()
    bom = load_bom(BOM)
    task = (
        "Assemble the blinky circuit: seat the breadboard and ESP32, then place "
        "the red LED with its 330 ohm series resistor beside it."
    )
    result = AssemblyAgent(bench).run(task, bom)

    print(f"engine: {'Claude' if result.used_llm else 'offline planner'}\n")
    for line in result.transcript:
        print(line)
    print("\n" + ("DONE: " if result.completed else "INCOMPLETE: ") + result.summary)


if __name__ == "__main__":
    main()
