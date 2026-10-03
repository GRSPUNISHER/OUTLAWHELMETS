"""Painter mesh for the 4-hole XP texture (Blender 4.5 headless:  blender -b --python _tools/xp4_painter_mesh.py).

User 2026-09-30: "still has the shadow on the xp 4-hole". XP_texturing.spp baked XP1's AO on the 3-hole shells, so the shell
under the 3-hole shroud frame is black; the 4-hole has no frame there and shows it. This mesh is the same set-up as
xp_painter.fbx but with the 4-hole shells (XP4 shell = XP1 + XP4M, XPC4 shell = Carbon1 + XP1 + XP4M) and the XP rails, same
texture-set names, so XP4_texturing.spp (a copy of XP_texturing.spp) can reload it with the user's stack intact and rebake XP1.
Writes _tools/work/xp/painter/xp4_painter.fbx.
"""
import bpy, os
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(TOOLS, "work", "xp", "fbx")
OUT = os.path.join(TOOLS, "work", "xp", "painter", "xp4_painter.fbx")
PARTS = {"XP4_Shell": "XP4_Shell", "XPC4_Shell": "XPC4_Shell", "XP_Rails": "XP_Rails"}

ITEM_SHIFT = (0.0, 0.02, -1.70)
OLD = os.path.join(TOOLS, "work", "xp", "painter", "xp_painter.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=OLD)
old = {o.name: o for o in bpy.data.objects if o.type == "MESH"}


def centre(o):
    import numpy as np
    return np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]).mean(0)


ASIDE = float(centre(old["XPC3_Shell_Carbon1"])[0] - centre(old["XP3_Shell"])[0])
REF_C = centre(old["XP3_Shell"])
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
print("OLD LAYOUT carbon shell aside by %.4f" % ASIDE)
keep = []
for part, name in PARTS.items():
    b = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(F, part + ".fbx"))
    new = [o for o in bpy.data.objects if o not in b]
    mesh = next(o for o in new if o.type == "MESH" and not o.name.startswith(("UTM", "UCX")))
    mw = mesh.matrix_world.copy()
    mesh.parent = None
    mesh.data.transform(mw)
    mesh.data.transform(Matrix.Translation(Vector(ITEM_SHIFT) + Vector((ASIDE if part == "XPC4_Shell" else 0.0, 0.0, 0.0))))
    mesh.matrix_world.identity()
    mesh.modifiers.clear(); mesh.vertex_groups.clear()
    mesh.name = name
    for o in new:
        if o is not mesh:
            bpy.data.objects.remove(o, do_unlink=True)
    keep.append(mesh)
for o in keep:
    for i, m in enumerate(o.data.materials):
        base = m.name.split(".")[0]
        o.data.materials[i] = bpy.data.materials.get(base) or bpy.data.materials.new(base)
        if bpy.data.materials[base] is not m and m.users == 0:
            bpy.data.materials.remove(m)
    print("OBJ", o.name, len(o.data.vertices), [m.name for m in o.data.materials], [round(x, 3) for x in o.dimensions],
          "centre", [round(float(x), 4) for x in centre(o)])
print("XP3 shell centre in the old mesh", [round(float(x), 4) for x in REF_C])
bpy.ops.object.select_all(action='DESELECT')
for o in keep:
    o.select_set(True)
bpy.context.view_layer.objects.active = keep[0]
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, object_types={'MESH'}, add_leaf_bones=False, bake_anim=False,
                         mesh_smooth_type='FACE', apply_unit_scale=True, use_space_transform=True)
print("WROTE", OUT)
