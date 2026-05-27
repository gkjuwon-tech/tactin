// TacTin assembly bench -- parametric model
// ------------------------------------------------------------
// A desktop workbench for the AI robot-arm assembly cell:
//   * a work surface sized to the arm's reach,
//   * a bolt-down mount pad for the arm base,
//   * an overhead T-slot gantry carrying the camera + light bars,
//   * recessed ESD trays where the engineer drops loose parts.
//
// Units are millimetres. Render:
//   openscad -o bench.stl hardware/bench.scad
//   openscad -o bench.png --imgsize=1200,900 hardware/bench.scad
// ------------------------------------------------------------

$fn = 48;

// ---- Top-level parameters ----------------------------------
bench_w        = 700;   // work surface width  (X)
bench_d        = 500;   // work surface depth  (Y)
top_thickness  = 18;    // tabletop board thickness
work_height    = 760;   // floor -> work surface (standard bench height)

leg            = 40;    // square leg cross-section
inset          = 45;    // leg inset from the edges

arm_pad_dia    = 160;   // diameter of the arm mount pad
arm_bolt_circle= 90;    // bolt circle for the arm base
arm_bolt_dia   = 6;     // M6 mount bolts
arm_pos        = [180, 250];  // arm base centre on the top (X,Y)

extrusion      = 20;    // 2020 T-slot side
gantry_height  = 420;   // camera height above the work surface
gantry_x       = 480;   // where the gantry uprights sit (X)

tray_w         = 150;   // ESD tray pocket
tray_d         = 110;
tray_depth     = 8;     // recess depth

// ---- Helpers ------------------------------------------------
module rounded_box(size, r) {
    hull() for (x = [r, size[0]-r], y = [r, size[1]-r])
        translate([x, y, 0]) cylinder(h = size[2], r = r);
}

// ---- Tabletop ----------------------------------------------
module tabletop() {
    difference() {
        color("BurlyWood") rounded_box([bench_w, bench_d, top_thickness], 14);
        // arm mount bolt pattern (clearance holes through the top)
        translate([arm_pos[0], arm_pos[1], -1])
            for (a = [0:90:359])
                rotate([0, 0, a])
                    translate([arm_bolt_circle/2, 0, 0])
                        cylinder(h = top_thickness + 2, d = arm_bolt_dia);
        // centre cable pass-through under the arm
        translate([arm_pos[0], arm_pos[1], -1])
            cylinder(h = top_thickness + 2, d = 30);
        // two recessed ESD part trays on the right-hand side
        for (j = [0:1])
            translate([bench_w - tray_w - 40,
                       60 + j * (tray_d + 30),
                       top_thickness - tray_depth])
                rounded_box([tray_w, tray_d, tray_depth + 1], 8);
    }
}

// ---- Arm mount pad (raised, flat, true-Z reference) --------
module arm_pad() {
    color("DimGray")
    translate([arm_pos[0], arm_pos[1], top_thickness])
    difference() {
        cylinder(h = 10, d = arm_pad_dia);
        translate([0, 0, -1])
            for (a = [0:90:359])
                rotate([0, 0, a])
                    translate([arm_bolt_circle/2, 0, 0])
                        cylinder(h = 12, d = arm_bolt_dia);
    }
}

// ---- Legs ---------------------------------------------------
module legs() {
    color("SaddleBrown")
    for (x = [inset, bench_w - inset - leg],
         y = [inset, bench_d - inset - leg])
        translate([x, y, -work_height + top_thickness])
            cube([leg, leg, work_height - top_thickness]);
}

// ---- 2020 extrusion (visual stand-in) ----------------------
module tslot(len) {
    color("Silver") cube([extrusion, extrusion, len]);
}

// ---- Overhead gantry: two uprights + cross beam ------------
module gantry() {
    z0 = top_thickness;
    // uprights at the back two corners of the camera span
    for (y = [80, bench_d - 80 - extrusion])
        translate([gantry_x, y, z0]) rotate([0, 0, 0])
            translate([0, 0, 0]) // upright grows in +Z
                color("Silver") cube([extrusion, extrusion, gantry_height]);
    // cross beam spanning the two uprights
    translate([gantry_x, 80, z0 + gantry_height - extrusion])
        color("Silver") cube([extrusion, bench_d - 160, extrusion]);
    // camera mount block hanging at mid-span, looking down at the arm
    translate([gantry_x - 30, bench_d/2 - 25, z0 + gantry_height - extrusion - 35])
        color("Black") cube([60, 50, 35]);
    // two light bars flanking the camera
    for (dy = [-90, 90])
        translate([gantry_x - 60, bench_d/2 + dy - 8, z0 + gantry_height - extrusion - 12])
            color("White") cube([120, 16, 10]);
}

// ---- Reach footprint (engraved guide, not structural) ------
module reach_guide() {
    color("OliveDrab", 0.35)
    translate([arm_pos[0], arm_pos[1], top_thickness + 0.2])
        difference() {
            cylinder(h = 0.6, r = 320);   // max reach
            translate([0, 0, -0.1]) cylinder(h = 0.8, r = 60);  // dead zone
        }
}

// ---- Assembly ----------------------------------------------
module bench() {
    tabletop();
    arm_pad();
    legs();
    gantry();
    reach_guide();
}

bench();
