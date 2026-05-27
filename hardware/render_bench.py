"""Photoreal render of the TacTin assembly bench (Blender + Cycles).

Run headless:
    blender -b -P hardware/render_bench.py

Builds the bench as real meshes with procedural/PBR materials, lights it with
an HDRI plus a key and a rim light, and renders with Cycles + denoise.
Output: hardware/bench_render.png
"""

import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
HDRI = os.path.join(HERE, "assets", "studio_small_08_2k.hdr")
OUT = os.path.join(HERE, "bench_render.png")


# ----------------------------------------------------------------------
# Scene reset
# ----------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ----------------------------------------------------------------------
# Material helpers
# ----------------------------------------------------------------------
def _set(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def principled(name, base, metallic=0.0, roughness=0.5, emission=None,
               emission_strength=0.0, anisotropic=0.0, coat=0.0, ior=1.45):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    _set(bsdf, "Base Color", (*base, 1.0))
    _set(bsdf, "Metallic", metallic)
    _set(bsdf, "Roughness", roughness)
    _set(bsdf, "Anisotropic", anisotropic)
    _set(bsdf, "Coat Weight", coat)
    _set(bsdf, "IOR", ior)
    if emission is not None:
        _set(bsdf, "Emission Color", (*emission, 1.0))
        _set(bsdf, "Emission Strength", emission_strength)
    return mat


def wood_material(name, light=(0.42, 0.26, 0.13), dark=(0.20, 0.11, 0.05)):
    """Procedural oak-ish wood: wave bands + noise grain, bump and roughness."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    _set(bsdf, "Coat Weight", 0.15)

    tex = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.0, 0.6, 1.0)
    links.new(tex.outputs["Object"], mapping.inputs["Vector"])

    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.inputs["Scale"].default_value = 1.3
    wave.inputs["Distortion"].default_value = 3.0
    wave.inputs["Detail"].default_value = 3.0
    wave.inputs["Detail Scale"].default_value = 1.2
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])

    grain = nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 18.0
    grain.inputs["Detail"].default_value = 6.0
    links.new(mapping.outputs["Vector"], grain.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    links.new(wave.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # roughness varies a touch with grain
    rramp = nodes.new("ShaderNodeValToRGB")
    rramp.color_ramp.elements[0].color = (0.30, 0.30, 0.30, 1)
    rramp.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
    links.new(grain.outputs["Fac"], rramp.inputs["Fac"])
    links.new(rramp.outputs["Color"], bsdf.inputs["Roughness"])

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    links.new(wave.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# ----------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------
def _finish(obj, material, bevel=0.0, smooth=False):
    if material:
        obj.data.materials.append(material)
    if bevel > 0:
        m = obj.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = 3
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(40)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
        try:
            obj.data.use_auto_smooth = True
            obj.data.auto_smooth_angle = math.radians(35)
        except Exception:
            pass
    return obj


def box(name, size, loc, rot=(0, 0, 0), material=None, bevel=0.004):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(obj, material, bevel)


def cyl(name, radius, depth, loc, rot=(0, 0, 0), material=None, bevel=0.002, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc,
                                         rotation=rot, vertices=verts)
    obj = bpy.context.active_object
    obj.name = name
    return _finish(obj, material, bevel, smooth=True)


# ----------------------------------------------------------------------
# Build the bench
# ----------------------------------------------------------------------
def build():
    wood = wood_material("Wood")
    leg_wood = wood_material("LegWood", light=(0.30, 0.18, 0.09), dark=(0.14, 0.08, 0.03))
    alu = principled("Aluminium", (0.78, 0.79, 0.82), metallic=1.0, roughness=0.22, anisotropic=0.5)
    dark_metal = principled("DarkMetal", (0.08, 0.085, 0.09), metallic=1.0, roughness=0.35)
    black_plastic = principled("BlackPlastic", (0.02, 0.02, 0.025), metallic=0.0, roughness=0.4, coat=0.3)
    white_plastic = principled("WhitePlastic", (0.82, 0.83, 0.85), metallic=0.0, roughness=0.3, coat=0.4)
    esd = principled("ESDMat", (0.05, 0.10, 0.13), metallic=0.0, roughness=0.6)
    led_red = principled("LED", (0.6, 0.02, 0.02), emission=(1.0, 0.05, 0.05), emission_strength=3.0, roughness=0.1)
    pcb = principled("PCB", (0.04, 0.22, 0.10), metallic=0.1, roughness=0.4, coat=0.2)
    resistor = principled("Resistor", (0.75, 0.66, 0.45), roughness=0.5)
    emit = principled("Emit", (1, 1, 1), emission=(1.0, 0.98, 0.95), emission_strength=18.0)

    TOP_Z = 0.75
    TH = 0.02

    # tabletop
    box("Top", (0.74, 0.50, TH), (0, 0, TOP_Z - TH / 2), material=wood, bevel=0.006)

    # legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx = sx * (0.74 / 2 - 0.05)
            ly = sy * (0.50 / 2 - 0.05)
            box(f"Leg_{sx}_{sy}", (0.04, 0.04, TOP_Z - TH),
                (lx, ly, (TOP_Z - TH) / 2), material=leg_wood, bevel=0.003)
    # apron rails
    box("ApronX", (0.66, 0.03, 0.06), (0, -0.23, TOP_Z - TH - 0.05), material=leg_wood, bevel=0.003)
    box("ApronX2", (0.66, 0.03, 0.06), (0, 0.23, TOP_Z - TH - 0.05), material=leg_wood, bevel=0.003)

    # arm mount pad (dark metal disc + bolt heads)
    pad = (-0.17, 0.0)
    cyl("Pad", 0.08, 0.012, (pad[0], pad[1], TOP_Z + 0.006), material=dark_metal, bevel=0.002)
    for a in range(0, 360, 90):
        bx = pad[0] + 0.055 * math.cos(math.radians(a))
        by = pad[1] + 0.055 * math.sin(math.radians(a))
        cyl(f"Bolt_{a}", 0.006, 0.008, (bx, by, TOP_Z + 0.014), material=alu, bevel=0.0008, verts=16)

    build_arm(pad, TOP_Z, white_plastic, dark_metal, alu)

    # ESD trays (recessed look: dark bottom + raised rim)
    for j, cy in enumerate((-0.12, 0.10)):
        cx = 0.20
        box(f"TrayBottom_{j}", (0.16, 0.11, 0.004), (cx, cy, TOP_Z + 0.002), material=esd, bevel=0.001)
        # rim
        for dx, dy, sxw, syw in (( 0.08, 0, 0.008, 0.118), (-0.08, 0, 0.008, 0.118),
                                  (0, 0.057, 0.176, 0.008), (0, -0.057, 0.176, 0.008)):
            box(f"Rim_{j}_{dx}_{dy}", (sxw, syw, 0.01), (cx + dx, cy + dy, TOP_Z + 0.005),
                material=dark_metal, bevel=0.0015)

    # a few loose parts in the trays (sells the story)
    cyl("LEDpart", 0.004, 0.012, (0.17, -0.12, TOP_Z + 0.01), rot=(math.radians(90), 0, 0.3),
        material=led_red, bevel=0.0005, verts=20)
    cyl("Rpart", 0.0025, 0.02, (0.23, -0.10, TOP_Z + 0.008), rot=(0, math.radians(90), 0.6),
        material=resistor, bevel=0.0004, verts=16)
    box("PCBpart", (0.05, 0.035, 0.0015), (0.20, 0.10, TOP_Z + 0.006), rot=(0, 0, 0.2), material=pcb, bevel=0.0008)

    build_gantry(TOP_Z, alu, black_plastic, emit)

    # studio backdrop sweep
    backdrop()


def build_arm(pad, top_z, plastic, joint, alu):
    """A connected cobot-style arm reaching forward over the work zone.

    Segments overlap their joints so the chain reads as one solid object.
    """
    bx, by = pad
    base_z = top_z + 0.012

    cyl("ArmBase", 0.05, 0.04, (bx, by, base_z + 0.02), material=plastic, bevel=0.004)
    # vertical column
    col_z = base_z + 0.04 + 0.06
    cyl("Column", 0.036, 0.13, (bx, by, col_z), material=plastic, bevel=0.004)
    shoulder = Vector((bx, by, base_z + 0.04 + 0.12))
    cyl("Shoulder", 0.042, 0.085, shoulder, rot=(math.radians(90), 0, 0), material=joint, bevel=0.003)

    # upper arm: 35 deg from vertical toward +X
    a1 = math.radians(35)
    d1 = Vector((math.sin(a1), 0, math.cos(a1)))
    L1 = 0.20
    up_c = shoulder + d1 * (L1 / 2)
    box("UpperArm", (0.052, 0.06, L1 + 0.05), tuple(up_c), rot=(0, a1, 0), material=plastic, bevel=0.006)
    elbow = shoulder + d1 * L1
    cyl("Elbow", 0.034, 0.072, tuple(elbow), rot=(math.radians(90), 0, 0), material=joint, bevel=0.003)

    # forearm: angled down-forward toward the trays
    a2 = math.radians(118)
    d2 = Vector((math.sin(a2), 0, math.cos(a2)))
    L2 = 0.22
    fa_c = elbow + d2 * (L2 / 2)
    box("Forearm", (0.044, 0.05, L2 + 0.05), tuple(fa_c), rot=(0, a2, 0), material=plastic, bevel=0.005)
    wrist = elbow + d2 * L2

    cyl("Wrist", 0.026, 0.05, tuple(wrist), rot=(math.radians(90), 0, 0), material=joint, bevel=0.002)
    tool_top = wrist + Vector((0, 0, -0.03))
    cyl("Tool", 0.009, 0.07, (tool_top.x, tool_top.y, tool_top.z - 0.02), material=alu, bevel=0.001, verts=24)
    cyl("Nozzle", 0.004, 0.025, (tool_top.x, tool_top.y, tool_top.z - 0.065), material=joint, bevel=0.0005, verts=16)


def build_gantry(top_z, alu, plastic, emit):
    up_x = 0.10
    h = 0.42
    for sy in (-0.18, 0.18):
        box(f"Upright_{sy}", (0.02, 0.02, h), (up_x, sy, top_z + h / 2), material=alu, bevel=0.0015)
    box("CrossBeam", (0.02, 0.40, 0.02), (up_x, 0, top_z + h - 0.01), material=alu, bevel=0.0015)
    # camera housing over the work centre, looking down
    box("CamBody", (0.06, 0.05, 0.04), (up_x - 0.04, 0, top_z + h - 0.05), material=plastic, bevel=0.004)
    cyl("CamLens", 0.018, 0.03, (up_x - 0.04, 0, top_z + h - 0.085), material=plastic, bevel=0.002, verts=32)
    # light bars flanking the camera
    for dy in (-0.10, 0.10):
        box(f"LightBar_{dy}", (0.12, 0.016, 0.012), (up_x - 0.04, dy, top_z + h - 0.07), material=emit, bevel=0.001)


def backdrop():
    # large curved-ish sweep made of a floor + a back plane, neutral grey
    grey = principled("Backdrop", (0.62, 0.63, 0.66), roughness=0.7)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 1.6, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.data.materials.append(grey)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 2.2, 2.5), rotation=(math.radians(90), 0, 0))
    back = bpy.context.active_object
    back.name = "BackWall"
    back.data.materials.append(grey)


# ----------------------------------------------------------------------
# Lighting, camera, world
# ----------------------------------------------------------------------
def setup_world():
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.45
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(HDRI)
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0, 0, math.radians(40))
    texco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(texco.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])


def add_light(name, kind, loc, energy, size, target):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    if kind == "AREA":
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.collection.objects.link(obj)
    c = obj.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return obj


def setup_camera_lights():
    target = bpy.data.objects.new("Target", None)
    target.location = (0.0, 0.0, 0.60)
    bpy.context.collection.objects.link(target)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 2.4
    cam_data.dof.aperture_fstop = 11.0
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (1.5, -1.8, 1.05)
    bpy.context.collection.objects.link(cam)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    bpy.context.scene.camera = cam

    # key (front-left, casts the grounding shadow), rim (back-right edge), soft fill
    add_light("Key", "AREA", (-0.9, -1.0, 1.8), 260, 1.5, target)
    add_light("Rim", "AREA", (1.2, 1.1, 1.5), 200, 0.6, target)
    add_light("Fill", "AREA", (0.4, -0.7, 2.1), 35, 2.5, target)


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    # This Blender build ships without OpenImageDenoise, so denoise is off and
    # we lean on a higher sample count plus adaptive sampling to stay clean.
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.samples = 600
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1050
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = OUT
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def main():
    reset_scene()
    build()
    setup_world()
    setup_camera_lights()
    setup_render()
    bpy.ops.render.render(write_still=True)
    print("WROTE", OUT)


main()
