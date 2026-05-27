# TacTin Workbench — Hardware Bill of Materials (v1)

The shopping list to physically build one **TacTin** assembly bench. Prices are
rough USD street prices for a single unit, early-2026, for budgeting only.
Two tiers are given where it matters: **Dev/MVP** (cheapest thing that proves
the loop) and **Pilot** (what you'd actually ship to a paying B2B customer).

---

## 1. Robot arm (the core)

| Part | Example product | Why | Qty | ~Price |
|------|-----------------|-----|----:|-------:|
| Desktop arm — MVP | Elephant Robotics **myCobot 280 Pi** | 6-DOF, Python/ROS SDK, cheap, fine for proving pick-and-place | 1 | $700 |
| Desktop arm — Pilot | **Dobot MG400** (4-axis SCARA) | 0.05 mm repeatability, 750 g payload, fast — the right tool for seating THT parts on a board | 1 | $2,000 |
| Desktop arm — Premium | **UFACTORY xArm 6** | 6-DOF, 0.1 mm, larger envelope, force feedback for delicate insertions | 1 | $6,500 |

> Repeatability is the spec that matters: pick-and-place of a 5 mm LED needs
> ≤0.1 mm. SCARA arms (MG400) beat hobby 6-DOF arms here, which is why the
> Pilot tier switches to it.

## 2. End effector

| Part | Example product | Notes | Qty | ~Price |
|------|-----------------|-------|----:|-------:|
| Vacuum pick nozzle + pump | 12 V diaphragm pump + 0.5 mm nozzle kit | Best for ICs / SMD / flat parts; gentler than a gripper | 1 | $60 |
| Parallel gripper | Vendor adaptive electric gripper | For through-hole parts, connectors, wires | 1 | $200 |
| Tool changer (Pilot) | Magnetic quick-change mount | Swap vacuum ↔ gripper ↔ iron without re-homing | 1 | $150 |
| Soldering iron (v2) | **Pinecil V2** on custom mount | Through-hole joints; needs the OpenSCAD iron-mount bracket | 1 | $40 |

## 3. Vision

| Part | Example product | Notes | Qty | ~Price |
|------|-----------------|-------|----:|-------:|
| Overhead camera | **Arducam global-shutter USB3** (or Basler ace for Pilot) | Global shutter = no motion blur while the arm moves; fixed mount on the gantry | 1 | $120 / $450 |
| Lens | 8 mm / 12 mm C-mount | Pick FoV to cover the full bench top | 1 | $60 |
| Wrist camera (optional) | Small USB module | Close-up confirmation of seating before solder | 1 | $40 |
| Ring / bar lighting | Diffuse LED bar, 5000 K | Kills shadows so detection is stable | 2 | $50 |
| Calibration target | Printed **ChArUco** board on rigid PVC | Hand-eye calibration (`tactin.vision.calibration`) | 1 | $20 |

## 4. Part presentation

| Part | Example product | Notes | Qty | ~Price |
|------|-----------------|-------|----:|-------:|
| ESD component trays | Anti-static partitioned trays | Engineer drops parts here; reduces detection ambiguity | 4 | $40 |
| Anti-static mat | ESD bench mat + wrist strap | Protects the parts being assembled | 1 | $35 |
| Tape feeder (v2/Pilot) | SMD tape-and-reel feeder | Presents 0402/0603 parts in known orientation | 2 | $300 |

## 5. Compute

| Part | Example product | Notes | Qty | ~Price |
|------|-----------------|-------|----:|-------:|
| Edge compute | **NVIDIA Jetson Orin Nano** | Runs the vision detector on-device; low latency | 1 | $500 |
| Or: mini-PC + GPU | Intel NUC + external GPU | If you'd rather run inference + the agent host together | 1 | $900 |

> The LLM agent loop (`tactin.agent`) calls the Claude API over the network, so
> the local box only needs to run the **vision** model and the motion control.

## 6. Frame, safety & misc

| Part | Example product | Notes | Qty | ~Price |
|------|-----------------|-------|----:|-------:|
| Bench top | CNC/laser-cut from `hardware/bench.scad` | The desk this whole thing bolts to | 1 | $80 |
| Aluminium extrusion | 2020 T-slot, ~3 m + brackets | Gantry that holds camera + lights overhead | 1 | $70 |
| E-stop button | Latching NC emergency stop | **Mandatory.** Cuts arm power on press | 1 | $20 |
| PSU + cabling | 24 V / 12 V bricks, USB, ESD-safe | | 1 | $80 |
| Fume extractor (v2) | Mini solder fume extractor + filter | Needed once soldering is enabled | 1 | $60 |

---

## Rough unit cost

| Tier | Ballpark BOM cost |
|------|------------------:|
| **Dev / MVP** (myCobot, vacuum, USB cam, Jetson) | **~$1,800** |
| **Pilot** (MG400, tool changer, machine-vision cam, feeders, gantry) | **~$5,500** |
| **Premium** (xArm 6, full vision + safety) | **~$9,500+** |

These are component costs only — not the sale price. The value sold to a B2B
customer is *hours of engineer time not spent hand-soldering prototypes*, so
price against that, not against the BOM.
