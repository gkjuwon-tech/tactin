// TACTIN workbench — parametric benchtop fixture for the pick-and-place arm.
//
// A rigid work surface with: an arm mounting boss at the back-centre, an
// overhead gantry holding the downward-looking camera centred over the work
// zone, four ArUco calibration pads at the corners of that zone, and a row of
// part-feeder tray cells along the front edge.
//
// Frame matches the software (tactin.geometry): origin at the arm base on the
// surface top, +X toward the front of the bench (toward the work zone), +Y to
// the operator's left, +Z up. The reachable work area is X 70..300, Y +-150.
//
// Render:  openscad -o workbench.stl hardware/workbench.scad
//          openscad -o workbench.png --viewall --autocenter hardware/workbench.scad

$fn = 48;

// ---- parameters (mm) -------------------------------------------------------
bench_depth   = 400;   // X, front-back
bench_width   = 600;   // Y, left-right
surface_t     = 18;    // work-surface thickness
foot_h        = 35;    // benchtop standoff feet
foot          = 40;    // foot footprint

arm_base_inset = 60;   // arm boss distance from the back edge
arm_boss_d     = 90;   // arm mounting boss diameter
arm_boss_h     = 14;

gantry_post    = 30;   // gantry post cross-section
gantry_h       = 470;  // camera height above the surface
cam_plate      = 90;   // camera mount plate size
cam_x          = 190;  // camera centred over the middle of the work zone (X)

tray_cells     = 6;
tray_cell      = 55;
tray_depth     = 45;
tray_wall      = 3;

aruco_pad      = 36;
aruco_pad_h    = 2;

// Work-zone corners (for the calibration pads), in the software frame.
work_x0 = 70;  work_x1 = 300;
work_y0 = -150; work_y1 = 150;

// A box centred in X/Y, resting with its base at z = zbase.
module box(sx, sy, sz, x, y, zbase) {
    translate([x, y, zbase + sz/2]) cube([sx, sy, sz], center = true);
}

// ---- parts -----------------------------------------------------------------
// The surface top is z=0; the slab hangs below it. The arm base is at (0,0,0).
module work_surface() {
    color("BurlyWood")
        box(bench_depth, bench_width, surface_t,
            bench_depth/2 - arm_base_inset, 0, -surface_t);
}

module feet() {
    fx0 = -arm_base_inset + foot/2 + 8;
    fx1 = bench_depth - arm_base_inset - foot/2 - 8;
    fy  = bench_width/2 - foot/2 - 8;
    color("DimGray")
        for (p = [[fx0,-fy],[fx0,fy],[fx1,-fy],[fx1,fy]])
            box(foot, foot, foot_h, p[0], p[1], -surface_t - foot_h);
}

module arm_mount() {
    color("SteelBlue") {
        cylinder(d = arm_boss_d, h = arm_boss_h);
        for (a = [45 : 90 : 315])
            rotate([0, 0, a]) translate([arm_boss_d/2 - 12, 0, 0])
                cylinder(d = 5, h = arm_boss_h + 1);
    }
}

module gantry() {
    px = -arm_base_inset + gantry_post/2;
    py = bench_width/2 - gantry_post/2 - 6;
    color("Gainsboro") {
        box(gantry_post, gantry_post, gantry_h, px, -py, 0);   // left post
        box(gantry_post, gantry_post, gantry_h, px,  py, 0);   // right post
        box(gantry_post, bench_width - 12, gantry_post,        // cross-beam
            px, 0, gantry_h - gantry_post);
        box(cam_x + arm_base_inset, gantry_post, gantry_post,  // forward boom
            (cam_x - arm_base_inset)/2, 0, gantry_h - gantry_post);
    }
    camera_mount();
}

module camera_mount() {
    color("DarkSlateGray")
        box(cam_plate, cam_plate, 6, cam_x, 0, gantry_h - gantry_post - 6);
    color("Black")
        translate([cam_x, 0, gantry_h - gantry_post - 6 - 16]) cylinder(d = 26, h = 16);
}

module tray_rail() {
    rail_w = tray_cells * tray_cell + tray_wall;
    translate([bench_depth - arm_base_inset - tray_depth - 10, -rail_w/2, 0])
        color("DarkKhaki")
        difference() {
            cube([tray_depth, rail_w, 22]);
            for (i = [0 : tray_cells - 1])
                translate([tray_wall, tray_wall + i*tray_cell, 6])
                    cube([tray_depth - 2*tray_wall, tray_cell - tray_wall, 20]);
        }
}

module aruco_pads() {
    color("White")
        for (p = [[work_x0,work_y0],[work_x0,work_y1],[work_x1,work_y1],[work_x1,work_y0]])
            box(aruco_pad, aruco_pad, aruco_pad_h, p[0], p[1], 0);
}

module work_zone_outline() {
    w = work_x1 - work_x0;
    h = work_y1 - work_y0;
    color("Sienna")
    translate([(work_x0 + work_x1)/2, 0, 0.4])  // sunk 0.2mm to avoid coplanar z-fight
        difference() {
            cube([w, h, 1.2], center = true);
            cube([w - 6, h - 6, 2.0], center = true);
        }
}

module workbench() {
    work_surface();
    feet();
    arm_mount();
    gantry();
    tray_rail();
    aruco_pads();
    work_zone_outline();
}

workbench();
