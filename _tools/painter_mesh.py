"""Painter mesh for texturing the Ballistic with the user's MCB HELMET.spp stack (Blender 4.5 headless).

  blender -b --python _tools/painter_mesh.py

The .spp's own embedded mesh (exported from Painter as spp_embedded_mesh.fbx) is kept FIRST and untouched: its masks
are per-face, so a rebuilt Bump with a different face order loses them. The Ballistic is appended as a separate
object, placed in the .spp frame (Kabsch fit of our Bump onto the embedded mesh by shared UVs) and moved aside so
bakes never see it overlapping. Writes _tools/work/painter/sf_painter.fbx.
"""
import bpy, os
import numpy as np
from mathutils import Matrix

TOOLS = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(TOOLS, "work", "fbx")
PD = os.path.join(TOOLS, "work", "painter")
OUT = os.path.join(PD, "sf_painter.fbx")


def imp(path):
    b = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in b]


def uv_points(o):
    me = o.data; uv = me.uv_layers[0].data; mw = o.matrix_world
    d = {}
    for li, l in enumerate(me.loops):
        d.setdefault((round(uv[li].uv[0], 5), round(uv[li].uv[1], 5)), tuple(mw @ me.vertices[l.vertex_index].co))
    return d


bpy.ops.wm.read_factory_settings(use_empty=True)
spp = [o for o in imp(os.path.join(PD, "spp_embedded_mesh.fbx")) if o.type == 'MESH']
print("SPP OBJECTS", [(o.name, len(o.data.vertices), len(o.data.polygons), [m.name for m in o.data.materials]) for o in spp])
bump = [o for o in imp(os.path.join(W, "SF_Bump_Item.fbx")) if o.type == 'MESH' and not o.name.startswith("UCX")][0]
rails = [o for o in imp(os.path.join(W, "SF_Rails_Item.fbx")) if o.type == 'MESH' and not o.name.startswith("UCX")][0]
bal = [o for o in imp(os.path.join(W, "SF_Ballistic_Item.fbx")) if o.type == 'MESH' and not o.name.startswith("UCX")][0]
for o in list(bpy.data.objects):
    if o.name.startswith("UCX"):
        bpy.data.objects.remove(o, do_unlink=True)

tgt = {}
for o in spp:
    tgt.update(uv_points(o))
src = {}
for o in (bump, rails):
    src.update(uv_points(o))
keys = [k for k in src if k in tgt]
A = np.array([src[k] for k in keys]); B = np.array([tgt[k] for k in keys])
ca, cb = A.mean(0), B.mean(0)
sa = np.sqrt(((A - ca) ** 2).sum(1).mean()); sb = np.sqrt(((B - cb) ** 2).sum(1).mean())
s = sb / sa
H = ((A - ca) * s).T @ (B - cb)
U, S, Vt = np.linalg.svd(H)
dd = np.sign(np.linalg.det(Vt.T @ U.T))
R = Vt.T @ np.diag([1, 1, dd]) @ U.T
t = cb - s * R @ ca
res = np.linalg.norm((s * (R @ A.T)).T + t - B, axis=1)
print("FIT matched", len(keys), "scale %.5f" % s, "rms %.6f max %.6f" % (np.sqrt((res ** 2).mean()), res.max()))
M = Matrix.Identity(4)
for i in range(3):
    for j in range(3):
        M[i][j] = s * R[i, j]
    M[i][3] = t[i]
span = B.max(0) - B.min(0)
off = Matrix.Translation((span[0] * 1.8, 0, 0))
bal.data.transform(off @ M @ bal.matrix_world)
bal.matrix_world = Matrix.Identity(4)
bal.name = "SF_Ballistic"
sfmat = spp[0].data.materials[0]
bal.data.materials.clear(); bal.data.materials.append(sfmat)
bpy.data.objects.remove(bump, do_unlink=True); bpy.data.objects.remove(rails, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for o in spp + [bal]:
    o.select_set(True)
bpy.context.view_layer.objects.active = spp[0]
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                         apply_unit_scale=True, use_space_transform=True, add_leaf_bones=False, bake_anim=False)
print("PAINTER MESH", OUT, "ballistic offset", round(span[0] * 1.8, 4))
