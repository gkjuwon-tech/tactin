# TACTIN — Project Brief

> **Vibe hardware for the engineer's workbench.** An AI agent that drives a
> desktop robot arm to assemble electronic prototypes from natural-language
> instructions — the physical-world counterpart to vibe coding.

---

## 1. The thesis

Value creation splits in two: moving **bits** (code, text, design) and moving
**atoms** (assembly, wiring, physical build). Over the last three years AI
collapsed the cost of moving bits — a prototype is now a 20-second prompt away.
Moving atoms is still 1985: a hardware engineer with tweezers, a magnifier, and
a steady hand, populating the same breadboard or test jig by hand for the
hundredth time.

The pieces to fix this already exist independently — physical AI, low-cost
robot arms, vision models, LLM tool-calling — but **nobody has pointed them at
the hardware developer's own bench.** Robotics money goes to the factory: cells
that do the *same* motion a million times, behind 5-figure KUKA/ABB arms. That
is the opposite of prototyping, which is *every build is different, quantity
one*. No one automates quantity-one. That is the gap TACTIN fills.

## 2. The product

A sub-$400 benchtop unit: a 5-DOF arm with a vacuum pickup nozzle, an overhead
camera, and the TACTIN software. The engineer drops components on the bench and
says what to build. Vision localizes the parts, Claude plans the pick-and-place
sequence as a tool-use loop, and the arm executes it — overnight, unattended,
while the engineer is asleep or doing design work.

It is explicitly **not** a factory cell and **not** a soldering robot. It is a
*copilot for the bench*: the physical equivalent of an IDE autocomplete, for
the part of hardware work that AI has so far left untouched.

## 3. Who buys it (B2B)

Individuals rarely buy hardware tools; companies expense them against engineer
time. The wedge:

| Segment | Pain today | TACTIN value |
|---------|-----------|--------------|
| Hardware startups | founders hand-build every prototype rev | unattended rev iteration |
| University / corporate R&D labs | grad students / techs populate test jigs by hand | free the humans for design |
| Test & measurement | repetitive jig population for DUT batches | overnight batch population |
| RC / drone / robotics builders | repetitive small-part placement | hands-free assembly |
| EE education | demonstrating circuits, repeatable lab setups | a teaching cell that builds on command |

Pricing intuition: a unit that runs unattended is measured against an
engineer's loaded hourly cost, not against a toy. One overnight 50-part job a
week pays the unit off inside a quarter.

## 4. Why now

- 5-DOF serial-bus servo arms (SO-ARM100 lineage, Feetech STS-class servos)
  dropped under $200 with open kinematics and good repeatability.
- LLM tool-calling matured into a reliable agent substrate — the model plans
  the sequence, the harness enforces the safety envelope.
- Vision + a single planar homography is enough to localize parts on a flat,
  calibrated bench; the LLM reads the overhead frame directly.

## 5. Why it's defensible

- **The moat is the agent + safety + calibration stack**, not the arm. Anyone
  can buy the arm; the value is the reliable language→motion loop that doesn't
  crash the nozzle into the bench.
- **Workload data flywheel:** every assembled prototype is a labelled
  language→layout→placement trace. That dataset improves planning and is not
  available to a hardware-only competitor.
- **Bench-native, not factory-native:** incumbents' margins come from
  integration billables on big cells; a self-calibrating $400 bench unit is
  structurally uninteresting for them to chase and cannibalize.

## 6. Architecture (this repository)

A working software stack that runs end-to-end in simulation today:

- Pure-Python core: closed-form 5-DOF kinematics, a safety envelope, a bench
  world model, and Cartesian motion planning — zero dependencies, fully tested.
- A Claude tool-use agent (`pick`, `place`, `move`, `look`, `add_slot`) with
  prompt caching on the frozen system + tool prefix.
- Vision: overhead camera abstraction + ArUco→bench homography.
- ESP32 firmware for servo-bus + vacuum control over USB.
- A parametric OpenSCAD workbench that renders to printable/cut parts.

The same `ArmController` API drives the simulation driver and the real
`SerialDriver`, so the agent and the safety envelope are validated long before
hardware is in the loop.

## 7. Roadmap

| Phase | Milestone |
|-------|-----------|
| P0 (here) | Sim-complete stack: kinematics, safety, agent loop, firmware, bench CAD |
| P1 | First physical unit; ArUco hand-eye calibration; vacuum tuning |
| P2 | Learned part detector (overhead) feeding the world model automatically |
| P3 | Tool-changer (gripper + nozzle); through-hole insertion; jig fixtures |
| P4 | Bench fleet + shared workload dataset; cloud planning improvements |

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Placement precision for fine-pitch parts | vacuum nozzle + closed-loop visual servoing in P2; start with ≥0603 / through-hole |
| "Why not a human?" on low volume | unattended overnight runs; the value is engineer time, not raw speed |
| LLM mis-plans a motion | every target passes the safety gate; out-of-envelope calls fail, they don't move the arm |
| Arm commoditization | moat is the agent/calibration stack + workload data, not the arm |
