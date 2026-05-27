"""Command-line entrypoint: `tactin`.

Subcommands:
    tactin scan                     -- scan the simulated bench and print parts
    tactin assemble "<task>" [bom]  -- run the assembly agent on a task
    tactin demo                     -- run the bundled blinky demo end to end
"""

from __future__ import annotations

import argparse
import logging
import sys

from .agent import AssemblyAgent
from .bench import BenchController
from .planning import load_bom


def _cmd_scan(_: argparse.Namespace) -> int:
    bench = BenchController()
    for part in bench.scan_table():
        print(f"{part.label:16s} x={part.world.x:6.1f}  y={part.world.y:6.1f}  conf={part.confidence:.2f}")
    return 0


def _cmd_assemble(args: argparse.Namespace) -> int:
    bench = BenchController()
    bom = load_bom(args.bom) if args.bom else None
    agent = AssemblyAgent(bench)
    result = agent.run(args.task, bom)
    _print_result(result)
    return 0 if result.completed else 1


def _cmd_demo(_: argparse.Namespace) -> int:
    bench = BenchController()
    agent = AssemblyAgent(bench)
    result = agent.run(
        "Build a blinky: seat the ESP32 and breadboard, then place the LED and "
        "its 330 ohm series resistor next to each other."
    )
    _print_result(result)
    return 0 if result.completed else 1


def _print_result(result) -> None:
    engine = "Claude" if result.used_llm else "offline planner"
    print(f"=== TacTin assembly ({engine}) ===")
    for line in result.transcript:
        print(line)
    print("-" * 40)
    print(("DONE: " if result.completed else "INCOMPLETE: ") + result.summary)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(prog="tactin", description="AI robot-arm assembly bench.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="scan the bench").set_defaults(func=_cmd_scan)

    p_asm = sub.add_parser("assemble", help="run the assembly agent")
    p_asm.add_argument("task", help="natural-language assembly task")
    p_asm.add_argument("bom", nargs="?", help="optional path to a BOM yaml file")
    p_asm.set_defaults(func=_cmd_assemble)

    sub.add_parser("demo", help="run the bundled blinky demo").set_defaults(func=_cmd_demo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
