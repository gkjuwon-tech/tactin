# TACTIN hardware

The reference workbench: a benchtop fixture that mounts the arm, holds the
overhead camera over the work zone, carries the ArUco calibration pads, and
provides part-feeder trays.

![workbench](workbench.png)

## Files

| File | What |
|------|------|
| `workbench.scad` | Parametric workbench — edit the parameters at the top and re-render |
| `workbench.png` | Rendered preview (above) |
| `workbench.stl` | Manifold mesh for the printable/cut parts |

## Render it yourself

```bash
# Mesh (no display needed):
openscad -o workbench.stl hardware/workbench.scad

# Preview image (headless: run under xvfb if you have no display):
xvfb-run -a openscad -o workbench.png --imgsize=1500,1100 \
  --colorscheme=Tomorrow --viewall --autocenter \
  --camera=0,0,0,60,0,28,0 --projection=perspective hardware/workbench.scad
```

Key parameters (top of `workbench.scad`): `bench_depth/width`, `gantry_h`
(camera height), `cam_x` (camera position over the work zone), `arm_base_inset`,
and the tray cell count/size.

## Coordinate frame

The CAD frame matches the software (`tactin.geometry`): origin at the arm base
on the surface top, **+X toward the front of the bench** (into the work zone),
**+Y to the operator's left**, **+Z up**. The reachable work area is
X 70–300 mm, Y ±150 mm — drawn as the sienna inlay rectangle on the surface.

## Wiring (firmware: `../firmware/tactin_arm_esp32`)

| Signal | ESP32 pin | To |
|--------|-----------|-----|
| Servo bus TX/RX | GPIO17 / GPIO16 (Serial2, 1 Mbps) | half-duplex adapter → STS3215 bus |
| Vacuum pump | GPIO25 | MOSFET module → pump |
| Solenoid valve | GPIO26 | MOSFET module → 3-way valve (vents to release) |
| Logic | USB | host PC running TACTIN |
| Power | — | 12V 5A to servo bus + pump; ESP32 from USB |

The host sends the line protocol (`M`/`V`/`H`) over USB; see
`tactin/arm/driver.py::SerialDriver` and the firmware header comment.

## Calibration (pixels → bench mm)

1. Print the four 36 mm ArUco markers and stick them on the white corner pads.
2. Capture an overhead frame; detect the four marker centres in pixels.
3. Build the homography from those four pixel points to their known bench
   coordinates (the work-zone corners):

   ```python
   from tactin.vision import BenchCalibration
   calib = BenchCalibration.from_markers(pixel_corners, bench_corners)
   x_mm, y_mm = calib.pixel_to_bench(px, py)
   ```

Because the bench is flat and the camera looks straight down, this single
planar homography localizes every part the detector reports.
