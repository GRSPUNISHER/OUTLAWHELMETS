"""Texel map for the Ballistic shell's own UV islands (Blender 4.5, headless):  blender -b --python _tools/map_ballistic.py

OUTLAW's SF_*_BCR/NMO were painted on the Bump (vendor "Carbon") + rails layout only; the Ballistic (vendor "SF") outer
and inner shell islands sit in atlas space nothing else uses, which holds only Painter padding. For every texel of those
islands that no Bump/rails triangle touches, find the matching point on the Bump shell (nearest, same facing) and store
its Bump UV. fill_ballistic.py then copies the painted colour across. Writes _tools/work/ballistic_map.npz.
"""
import bpy, bmesh, os
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(TOOLS, "work", "fbx")
RES = 2048


def load(n):
    b = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(W, n + "_Item.fbx"))
    return [o for o in bpy.data.objects if o not in b and o.type == 'MESH' and not o.name.startswith("UCX")][0]


def tris(o):
    """triangles (3D, UV) + per-triangle flag: True = the shell (largest-area mesh island), False = panels/pads."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv.active
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
    shell_id = int(np.argmax(areas))
    P, U = [], []
    for f in bm.faces:
        P.append([tuple(l.vert.co) for l in f.loops])
        U.append([tuple(l[uvl].uv) for l in f.loops])
    bm.free()
    return np.array(P), np.array(U), np.array(comp) == shell_id


def raster(U, res=RES):
    """yield (tri index, ix, iy, barycentric) for texel centres inside each UV triangle"""
    for t, uv in enumerate(U):
        px = uv * res
        px[:, 1] = res - px[:, 1]
        lo = np.floor(px.min(0)).astype(int); hi = np.ceil(px.max(0)).astype(int)
        lo = np.clip(lo, 0, res - 1); hi = np.clip(hi, 0, res - 1)
        xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1) + 0.5, np.arange(lo[1], hi[1] + 1) + 0.5)
        p = np.stack([xs.ravel(), ys.ravel()], 1)
        a, b, c = px
        v0, v1, v2 = b - a, c - a, p - a
        d = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(d) < 1e-12:
            continue
        w1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / d
        w2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / d
        w0 = 1 - w1 - w2
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if m.any():
            yield t, np.floor(p[m, 0]).astype(int), np.floor(p[m, 1]).astype(int), np.stack([w0[m], w1[m], w2[m]], 1)


bpy.ops.wm.read_factory_settings(use_empty=True)
bump, rails, bal = load("SF_Bump"), load("SF_Rails"), load("SF_Ballistic")
PB, UB, SB = tris(bump)
PR, UR, _ = tris(rails)
PS, US, SS = tris(bal)

used = np.zeros((RES, RES), bool)
for U in (UB, UR):
    for t, ix, iy, w in raster(U):
        used[iy, ix] = True
for _ in range(2):
    u = used.copy()
    u[1:] |= used[:-1]; u[:-1] |= used[1:]; u[:, 1:] |= used[:, :-1]; u[:, :-1] |= used[:, 1:]
    used = u

sb = set(map(tuple, np.round(UB.reshape(-1, 2), 4)))
own = [t for t in range(len(US)) if not all(tuple(q) in sb for q in np.round(US[t], 4))]
print("ballistic tris", len(US), "own-layout tris", len(own), "own shell", int(SS[own].sum()), "own panels", int((~SS[own]).sum()))

NB = np.cross(PB[:, 1] - PB[:, 0], PB[:, 2] - PB[:, 0]); NB /= np.linalg.norm(NB, axis=1, keepdims=True) + 1e-12


def bvh_of(sel):
    idx = np.where(sel)[0]
    t = BVHTree.FromPolygons([tuple(v) for v in PB[idx].reshape(-1, 3)], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(idx))])
    return t, idx


BVH = {True: bvh_of(SB), False: bvh_of(~SB)}          # shell texels copy from the Bump shell, panels from Bump panels
RADIUS = {True: 0.03, False: 0.06}

tex_x, tex_y, src_uv, src_p, src_n, gap, cls = [], [], [], [], [], [], []
miss = 0
for t, ix, iy, w in raster(US[own]):
    t = own[t]
    keep = ~used[iy, ix]
    if not keep.any():
        continue
    ix, iy, w = ix[keep], iy[keep], w[keep]
    n = np.cross(PS[t, 1] - PS[t, 0], PS[t, 2] - PS[t, 0]); n /= np.linalg.norm(n) + 1e-12
    pts = w @ PS[t]
    shell = bool(SS[t])
    bvh, remap = BVH[shell]
    for x, y, p in zip(ix, iy, pts):
        near = BVH[True][0].find_nearest(Vector(p))
        best = None
        for loc, nor, idx, dist in bvh.find_nearest_range(Vector(p), RADIUS[shell]):
            idx = int(remap[idx])
            if float(np.dot(NB[idx], n)) > 0.5 and (best is None or dist < best[2]):
                best = (loc, idx, dist)
        if best is None:
            miss += 1
            continue
        loc, idx, _ = best
        a, b, c = PB[idx]
        v0, v1, v2 = b - a, c - a, np.array(loc) - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        d20, d21 = v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        bv = (d11 * d20 - d01 * d21) / den; bw = (d00 * d21 - d01 * d20) / den
        uvp = (1 - bv - bw) * UB[idx, 0] + bv * UB[idx, 1] + bw * UB[idx, 2]
        tex_x.append(x); tex_y.append(y); src_uv.append(uvp); src_p.append(p); src_n.append(n); gap.append(near[3] if near[0] else 1.0); cls.append(shell)

np.savez_compressed(os.path.join(TOOLS, "work", "ballistic_map.npz"), x=np.array(tex_x), y=np.array(tex_y),
                    uv=np.array(src_uv), used=used, p=np.array(src_p), n=np.array(src_n), gap=np.array(gap), shell=np.array(cls))
print("mapped texels", len(tex_x), "no match", miss)
