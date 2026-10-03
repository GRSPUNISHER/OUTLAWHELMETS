"""Mark Ballistic texels that sit over a Bump vent hole (Blender 4.5 headless):  blender -b --python _tools/vent_mask.py

For every mapped texel (ballistic_map.npz: point P, normal N) cast a ray inward along -N from just outside the surface.
Covered = the first Bump-shell hit is an OUTWARD-facing face within 4 mm of the Ballistic surface. Anything else (hole
wall, inner surface, nothing) means the Bump has a vent there. Adds `hole` to ballistic_map.npz.
"""
import bpy, bmesh, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOOLS = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(TOOLS, "work", "ballistic_map.npz")

bpy.ops.wm.read_factory_settings(use_empty=True)
b = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=os.path.join(TOOLS, "work", "fbx", "SF_Bump_Item.fbx"))
o = [x for x in bpy.data.objects if x not in b and x.type == 'MESH' and not x.name.startswith("UCX")][0]
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.faces.ensure_lookup_table()
comp = [-1] * len(bm.faces); areas = []
for f in bm.faces:
    if comp[f.index] >= 0:
        continue
    k = len(areas); comp[f.index] = k; st = [f]; a = 0.0
    while st:
        g = st.pop(); a += g.calc_area()
        for e in g.edges:
            for h in e.link_faces:
                if comp[h.index] < 0:
                    comp[h.index] = k; st.append(h)
    areas.append(a)
shell = int(np.argmax(areas))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.index] != shell], context='FACES')
bvh = BVHTree.FromBMesh(bm)

m = dict(np.load(MAP))
P, N, SH = m["p"], m["n"], m["shell"]
hole = np.zeros(len(P), bool)
for i in np.where(SH)[0]:
    n = Vector(N[i]); p = Vector(P[i]) + n * 0.003
    loc, nor, idx, dist = bvh.ray_cast(p, -n, 0.007)
    hole[i] = loc is None or nor.dot(n) < 0.5
m["hole"] = hole
np.savez_compressed(MAP, **m)
print("shell texels", int(SH.sum()), "over a Bump vent", int(hole.sum()))
