# TACTIN — Bill of Materials (reference prototype, "Bench Unit v0")

Everything you need to build one TACTIN workbench. Costs are rough USD for a
single hobby/prototype unit; at production volume the arm + servos dominate and
drop substantially. The developer supplies the components being assembled — this
BOM is the *machine*, not its workload.

The 3D-printed brackets are generated from [`hardware/workbench.scad`](hardware/workbench.scad).

## 1. Robot arm + actuation

| # | Item | Spec | Qty | ~USD | Notes |
|---|------|------|-----|------|-------|
| 1 | 5-DOF servo arm kit | SO-ARM100 lineage / equivalent, printed links | 1 | 120 | Open-source arm; or print links + buy servos separately |
| 2 | Serial-bus servo | Feetech STS3215 (12V, 30 kg·cm, magnetic encoder) | 5 | 75 | One per joint; included if buying the kit above |
| 3 | Servo horn / hardware set | metal horns, M3 hardware | 1 | 8 | |

## 2. End effector — vacuum pickup

A vacuum nozzle (not a gripper) is the right tool for electronics: it handles
SMD parts, ICs, and small through-hole bodies from the top surface.

| # | Item | Spec | Qty | ~USD | Notes |
|---|------|------|-----|------|-------|
| 4 | Mini vacuum pump | 12V diaphragm, ≥ -55 kPa | 1 | 9 | |
| 5 | 3-way solenoid valve | 12V, vents nozzle for instant release | 1 | 7 | Energize to drop the part fast |
| 6 | Pick-and-place nozzle set | SMD vacuum needles + silicone cups (0.4–6 mm) | 1 | 8 | |
| 7 | Silicone tubing + fittings | 2 mm / 4 mm ID | 1 | 5 | |

## 3. Control + power

| # | Item | Spec | Qty | ~USD | Notes |
|---|------|------|-----|------|-------|
| 8 | ESP32 dev board | WROOM-32, dual UART | 1 | 7 | Runs `firmware/tactin_arm_esp32` |
| 9 | Servo bus adapter | Half-duplex TTL (Waveshare bus servo adapter, or 74HC126) | 1 | 6 | STS3215 single-wire bus ↔ ESP32 Serial2 |
| 10 | MOSFET switch module | logic-level, ≥ 5A (pump + solenoid) | 2 | 4 | Driven by ESP32 GPIO25/26 |
| 11 | PSU | 12V 5A, barrel + terminal | 1 | 14 | Servos + pump rail |
| 12 | Wiring / connectors | JST, ferrules, 18AWG | 1 | 8 | |

## 4. Vision + calibration

| # | Item | Spec | Qty | ~USD | Notes |
|---|------|------|-----|------|-------|
| 13 | Overhead camera | 1080p USB (Logitech C920 / Arducam) | 1 | 30 | Looks straight down at the bench |
| 14 | ArUco markers | printed 4×, 36 mm, on the corner pads | 1 | 0 | Defines the pixel→bench homography |

## 5. Structure (from `workbench.scad`)

| # | Item | Spec | Qty | ~USD | Notes |
|---|------|------|-----|------|-------|
| 15 | Work surface | 600×400×18 mm plywood/MDF (or laser-cut) | 1 | 12 | |
| 16 | Gantry extrusion | 2020 aluminium: 2× 500 mm posts, 1× 600 mm beam | 1 | 18 | Holds the camera over the work zone |
| 17 | Corner brackets | 2020 90° brackets + T-nuts | 1 | 6 | |
| 18 | 3D-printed parts | arm boss, camera plate, tray rail, feet | 1 | 5 | Printed from the SCAD model |
| 19 | Fastener kit | M3/M4 assortment | 1 | 6 | |

## 6. Optional — standalone compute

| # | Item | Spec | Qty | ~USD | Notes |
|---|------|------|-----|------|-------|
| 20 | Raspberry Pi 5 (8GB) | runs TACTIN headless | 1 | 80 | Skip if driving from the dev's PC |

---

## Cost summary

| Configuration | ~USD |
|---------------|------|
| Core machine (rows 1–19) | **≈ 360** |
| + standalone Pi compute | ≈ 440 |

> The developer's PC already runs the agent and vision, so a base unit is a
> sub-$400 add-on to a bench that pays for itself the first time the engineer
> leaves a 50-part tray-population job running overnight.
