"""TacTin -- Vibe Hardware: an AI robot-arm assembly bench.

The package is organised in layers, bottom to top:

    geometry  -> pure spatial math (poses, transforms)
    sim       -> a simulated physical world (table + parts + gripper)
    vision    -> cameras + part detection + camera->robot calibration
    robot     -> arm driver abstraction + motion skills (pick/place/solder)
    planning  -> bill-of-materials + assembly plan models
    agent     -> the LLM tool-calling loop that drives the bench

Everything runs headless against the simulator, so the whole stack works
without any hardware attached -- the "vibe coding for hardware" loop.
"""

__version__ = "0.1.0"
