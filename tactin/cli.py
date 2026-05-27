"""``tactin`` command-line entry point.

  tactin info        show the arm spec and work area
  tactin selftest    round-trip the kinematics across the workspace
  tactin demo        build a sample bench and run a scripted pick-and-place
                     (offline — uses the simulation driver, no API key needed)
  tactin run "..."   run the LLM agent on a sample bench (needs ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import math
import sys

from .arm.controller import ArmController
from .arm.driver import SimDriver
from .config import Config
from .geometry import Pose
from .kinematics import forward_kinematics, inverse_kinematics
from .workspace import Bench, Part, Slot


def demo_bench() -> Bench:
    """A representative bench: a few parts and a breadboard with placement rows."""

    bench = Bench()
    bench.add_part(Part("led1", "led", x=130, y=-90, label="red 5mm"))
    bench.add_part(Part("r1", "resistor", x=170, y=-90, label="330Ω"))
    bench.add_part(Part("r2", "resistor", x=210, y=-90, label="10kΩ"))
    bench.add_part(Part("esp1", "ic", x=150, y=120, label="ESP32", z=3.0))
    bench.add_part(Part("cap1", "capacitor", x=250, y=110, label="100nF"))
    for i in range(4):
        bench.add_slot(Slot(f"bb_row{i + 1}", x=180.0, y=-20.0 + i * 20.0, z=6.0))
    return bench


def cmd_info(_args: argparse.Namespace) -> int:
    cfg = Config()
    arm, area = cfg.arm, cfg.work_area
    print("TACTIN arm spec")
    print(f"  links (mm): base_height={arm.base_height} l1={arm.l1} l2={arm.l2} l3={arm.l3}")
    print(f"  max reach: {arm.max_reach:.0f} mm")
    print("work area (mm)")
    print(f"  x {area.x_min:.0f}..{area.x_max:.0f}, y {area.y_min:.0f}..{area.y_max:.0f}, "
          f"z {area.z_min:.0f}..{area.z_max:.0f}, travel {area.z_travel:.0f}")
    return 0


def cmd_selftest(_args: argparse.Namespace) -> int:
    cfg = Config()
    worst = 0.0
    tested = 0
    for x in range(80, 301, 20):
        for y in range(-160, 161, 40):
            for z in (10, 40, 80):
                pose = Pose(x=float(x), y=float(y), z=float(z))
                try:
                    joints = inverse_kinematics(pose, cfg.arm)
                except Exception:
                    continue
                back = forward_kinematics(joints, cfg.arm)
                err = math.dist(pose.as_xyz(), back.as_xyz())
                worst = max(worst, err)
                tested += 1
    print(f"kinematics round-trip: tested {tested} poses, worst error {worst:.2e} mm")
    return 0 if worst < 1e-6 else 1


def cmd_demo(_args: argparse.Namespace) -> int:
    cfg = Config()
    bench = demo_bench()
    driver = SimDriver()
    arm = ArmController(cfg, driver)
    arm.start()

    print("Initial bench:")
    print(bench.summary())
    print()

    # A scripted plan: LED + two resistors onto the breadboard rows.
    plan = [("led1", "bb_row1"), ("r1", "bb_row2"), ("r2", "bb_row3")]
    for part_id, slot_name in plan:
        part = bench.get_part(part_id)
        slot = bench.get_slot(slot_name)
        arm.pick_at(part.pick_pose())
        bench.mark_picked(part_id)
        arm.place_at(Pose(x=slot.x, y=slot.y, z=slot.z))
        bench.mark_placed(slot.x, slot.y, slot.z, slot=slot_name)
        print(f"placed {part_id} ({part.label}) -> {slot_name}")
    arm.park()
    arm.stop()

    print()
    print("Final bench:")
    print(bench.summary())
    print()
    print(f"driver issued {len(driver.transcript)} commands "
          f"({sum(c.startswith('move') for c in driver.transcript)} moves, "
          f"{sum(c.startswith('vacuum') for c in driver.transcript)} vacuum toggles)")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .agent.runner import VibeSession  # lazy: pulls in the SDK only here

    cfg = Config()
    bench = demo_bench()
    arm = ArmController(cfg, SimDriver())
    session = VibeSession(cfg, bench, arm)
    try:
        result = session.run(args.instruction)
    except Exception as exc:  # surface API/auth errors cleanly
        print(f"agent run failed: {exc}", file=sys.stderr)
        return 1
    print(result.final_text)
    print(f"\n[{result.steps} steps, {len(result.tool_calls)} tool calls]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tactin", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="show arm spec and work area").set_defaults(func=cmd_info)
    sub.add_parser("selftest", help="round-trip the kinematics").set_defaults(func=cmd_selftest)
    sub.add_parser("demo", help="scripted offline pick-and-place").set_defaults(func=cmd_demo)
    run_p = sub.add_parser("run", help="run the LLM agent (needs ANTHROPIC_API_KEY)")
    run_p.add_argument("instruction", help="what to build, in plain language")
    run_p.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
