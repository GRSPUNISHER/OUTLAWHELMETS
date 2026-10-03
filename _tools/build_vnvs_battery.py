"""Skinned OUTLAW-style worn model of the Vanguard GPNVG-18 battery pack.

The Vanguard battery is a rigid prop that Vanguard seats with a Head-pivot slot offset. OUTLAW's Battery slots carry no
offset (their battery models are skinned in character space), so this exports the Vanguard battery mesh at the seat
Vanguard measured on the OUTLAW SF shell (helmet_slots.json battery_seat_dec), skinned 100 % to the Head bone of the
OUTLAW template armature. Run: blender -b --python build_vnvs_battery.py
"""
import json
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(TOOLS, "template", "SF V2 Bump (Rigged).fbx")
VN = "D:/Projects/Vanguard-Night-Vision-Systems"
SRC = VN + "/Assets/NVG/GPNVG18/VNVS_GPNVG18_Battery.fbx"
SLOTS = VN + "/_tools/work/helmet_slots.json"
TEST_HELMET = VN + "/Assets/TestHelmet/VNVS_TestHelmet_SF.fbx"
BNVD = os.path.join(os.path.dirname(TOOLS), "SFHELMETS", "ASSETS", "Helmet Accessories", "BNVD BATTERY", "bnvdbattery.fbx")
CONTACT_BAND = 0.003
OUT_DIR = os.path.join(os.path.dirname(TOOLS), "SFHELMETS", "ASSETS", "Helmet Accessories", "GPNVG18 BATTERY")
OUT = os.path.join(OUT_DIR, "vnvs_gpnvg18_battery.fbx")
S = Matrix.Diagonal((-1, -1, 1, 1))


def imported(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return ([round(min(p[i] for p in pts), 4) for i in range(3)], [round(max(p[i] for p in pts), 4) for i in range(3)])


def world_verts(objs):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.type != "MESH":
            continue
        mesh = o.evaluated_get(dg).to_mesh()
        pts += [tuple(o.matrix_world @ v.co) for v in mesh.vertices]
    return np.array(pts)


def contact(pts):
    centre = pts.mean(0)
    _, vecs = np.linalg.eigh(np.cov((pts - centre).T))
    normal = vecs[:, 0]
    if normal[1] > 0:
        normal = -normal
    depth = (pts - centre) @ normal
    face = pts[depth <= depth.min() + CONTACT_BAND]
    return Vector(face.mean(0)), Vector(normal)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tpl = imported(TEMPLATE)
    arm = next(o for o in tpl if o.type == "ARMATURE")
    print("TEMPLATE_HELMET_BBOX", bbox(tpl))
    for o in tpl:
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    if os.path.exists(TEST_HELMET):
        test = imported(TEST_HELMET)
        print("VANGUARD_TEST_HELMET_BBOX", bbox(test))
        for o in test:
            bpy.data.objects.remove(o, do_unlink=True)

    seat = (S @ Vector(json.load(open(SLOTS))["battery_seat_dec"]).to_4d()).to_3d()
    src = imported(SRC)
    meshes = [o for o in src if o.type == "MESH"]
    for o in src:
        if o.parent is None:
            o.location += seat
    bpy.context.view_layer.update()
    battery = meshes[0]
    mw = battery.matrix_world.copy()
    battery.parent = None
    battery.matrix_world = mw
    for o in src:
        if o is not battery:
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    battery.select_set(True)
    bpy.context.view_layer.objects.active = battery
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bnvd = imported(BNVD)
    bnvd_pts = world_verts(bnvd)
    target_point, target_normal = contact(bnvd_pts)
    global BNVD_MIN, BNVD_MAX
    BNVD_MIN, BNVD_MAX = bnvd_pts.min(0), bnvd_pts.max(0)
    for o in bnvd:
        bpy.data.objects.remove(o, do_unlink=True)

    source_point, source_normal = contact(world_verts([battery]))
    rot = source_normal.rotation_difference(target_normal).to_matrix().to_4x4()
    battery.data.transform(Matrix.Translation(source_point) @ rot @ Matrix.Translation(-source_point))
    battery.data.update()
    pts = world_verts([battery])
    centre = Vector((pts.min(0) + pts.max(0)) / 2)
    target_centre = Vector((BNVD_MIN + BNVD_MAX) / 2)
    n = target_normal.normalized()
    tangent = (target_centre - centre) - n * (target_centre - centre).dot(n)
    depth = n * (target_point - source_point).dot(n)
    battery.data.transform(Matrix.Translation(tangent + depth))
    battery.data.update()
    print("BNVD_CONTACT", tuple(round(v, 4) for v in target_point), tuple(round(v, 3) for v in target_normal))
    print("MOVED_FROM", tuple(round(v, 4) for v in source_point), tuple(round(v, 3) for v in source_normal))
    battery.name = "VNVS_GPNVG18_Battery_OUTLAW"
    battery.data.name = battery.name
    for slot in battery.material_slots:
        if slot.material:
            slot.material.name = "VNVS_GPNVG18_Battery"
    print("BATTERY_BBOX", bbox([battery]), "SEAT", tuple(round(v, 4) for v in seat))

    battery.vertex_groups.clear()
    group = battery.vertex_groups.new(name="Head")
    group.add(list(range(len(battery.data.vertices))), 1.0, "REPLACE")
    battery.parent = arm
    battery.parent_type = "OBJECT"
    battery.matrix_world = Matrix.Identity(4)
    battery.modifiers.new("Armature", "ARMATURE").object = arm

    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in (arm, battery):
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
                             bake_anim=False, use_armature_deform_only=False, mesh_smooth_type="FACE",
                             apply_unit_scale=True, use_space_transform=True)
    print("EXPORTED", OUT, "verts", len(battery.data.vertices))


main()
