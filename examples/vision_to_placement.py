"""End-to-end (offline): camera detections -> bench coordinates -> assembly.

Shows the vision path the CLI demo skips: pretend the overhead detector found
three parts at pixel locations, localize them to the bench through the ArUco
homography, load them into the world model, then drive the simulation arm to
place them on a breadboard. No hardware, no API key.

    python examples/vision_to_placement.py
"""

from tactin.arm.controller import ArmController
from tactin.arm.driver import SimDriver
from tactin.config import Config
from tactin.geometry import Pose
from tactin.vision import BenchCalibration, Detection, detections_to_parts
from tactin.workspace import Bench, Slot


def main() -> None:
    cfg = Config()

    # 1. Calibrate: four ArUco markers (image pixels) -> work-zone corners (bench mm).
    pixels = [(40, 30), (600, 30), (600, 450), (40, 450)]
    bench_corners = [(70.0, 150.0), (300.0, 150.0), (300.0, -150.0), (70.0, -150.0)]
    calib = BenchCalibration.from_markers(pixels, bench_corners)

    # 2. The overhead detector reports parts in pixels (kind + marking + centre).
    detections = [
        Detection(kind="led", px=300, py=360, label="red 5mm"),
        Detection(kind="resistor", px=360, py=360, label="330Ω"),
        Detection(kind="ic", px=320, py=120, label="ATtiny85"),
    ]
    parts = detections_to_parts(detections, calib)

    # 3. Load the world model and define breadboard placement rows.
    bench = Bench()
    for part in parts:
        bench.add_part(part)
    for i in range(3):
        bench.add_slot(Slot(f"bb_row{i + 1}", x=180.0, y=-20.0 + i * 20.0, z=6.0))

    print("Localized parts:")
    print(bench.summary())
    print()

    # 4. Drive the (simulated) arm: place each part on a breadboard row.
    arm = ArmController(cfg, SimDriver())
    arm.start()
    for part, row in zip(parts, ["bb_row1", "bb_row2", "bb_row3"]):
        slot = bench.get_slot(row)
        from_x, from_y = part.x, part.y
        arm.pick_at(part.pick_pose())
        bench.mark_picked(part.id)
        arm.place_at(Pose(x=slot.x, y=slot.y, z=slot.z))
        bench.mark_placed(slot.x, slot.y, slot.z, slot=row)
        print(f"placed {part.id} ({part.label}) at {row} "
              f"(picked from bench {from_x:.0f},{from_y:.0f})")
    arm.stop()


if __name__ == "__main__":
    main()
