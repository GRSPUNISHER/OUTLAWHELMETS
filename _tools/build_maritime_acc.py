"""Maritime-only AMP / PVS-31 BRS / ShawBrain pouch from the user's fit (Blender 4.5 headless):

  blender -b --python _tools/build_maritime_acc.py

User 2026-09-30 re-placed and sculpted these three on the Maritime in _tools/work/maritime/Maritime_all_attachments_AOR1.blend
(saved copy: ..._userfix.blend; my untouched build: ..._orig.blend). They become separate "(Maritime)" items; the SF / XP keep
the originals. The user's world-space geometry is exported as-is (skinned to Head, OUTLAW template armature) plus an _Item
model (ITEM_SHIFT + UCX_Item hull; a box for the ShawBrain, whose hull had degenerate faces). Normals: the vendor custom normals are kept (rotated with any rigid move); only loops of
faces touching a sculpted vertex get recomputed normals. Writes _tools/work/maritime/fbx/MT_<part>.fbx / _Item.fbx.
"""
import os
_T = os.path.dirname(os.path.abspath(__file__))
_s = open(os.path.join(_T, "build_maritime.py"), encoding="utf-8").read()
exec(_s[_s.index("import bpy"):_s.index("def main():")])

W = os.path.join(TOOLS, "work", "maritime")
PARTS = {"Ops-Core AMP": "MT_AMP", "PVS-31 BRS": "MT_BRS", "ShawBrain Pouch (MC)": "MT_ShawBrain"}
BOX_ITEM = {"MT_ShawBrain"}


def box(obj, name):
    pts = np.array([tuple(obj.matrix_world @ v.co) for v in obj.data.vertices])
    lo, hi = pts.min(0), pts.max(0)
    bm = bmesh.new()
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            for z in (lo[2], hi[2]):
                bm.verts.new((x, y, z))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(bpy.data.materials.get(UCX_MAT) or bpy.data.materials.new(UCX_MAT))
    return o


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {}
    for n in PARTS:
        o = bpy.data.objects[n]
        R3 = np.array(o.matrix_world.to_3x3())
        V = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        N = np.array([tuple(c.vector) for c in o.data.corner_normals]) @ R3.T
        N /= np.linalg.norm(N, axis=1, keepdims=True)
        out[n] = (V, N)
    return out


orig = snapshot(os.path.join(W, "Maritime_all_attachments_AOR1_orig.blend"))
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, "Maritime_all_attachments_AOR1_userfix.blend"))
for o in list(bpy.data.objects):
    if o.name not in PARTS:
        bpy.data.objects.remove(o, do_unlink=True)
arm = import_template()
os.makedirs(os.path.join(W, "fbx"), exist_ok=True)
for name, part in PARTS.items():
    o = bpy.data.objects[name]
    o.hide_set(False); o.hide_render = False
    for i, m in enumerate(o.data.materials):
        base = m.name.split("|")[0]
        o.data.materials[i] = bpy.data.materials.get(base) or bpy.data.materials.new(base)
    me = o.data
    me.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    V = np.array([tuple(v.co) for v in me.vertices])
    V0, N0 = orig[name]
    fits = [(np.eye(3), 1.0, np.zeros(3))]
    R, t = kabsch(V0, V); fits.append((R, 1.0, t))
    c0, c1 = V0.mean(0), V.mean(0); s = np.sqrt(((V - c1) ** 2).sum() / ((V0 - c0) ** 2).sum())
    R, t = kabsch(V0 * s, V); fits.append((R, s, t))
    best = None
    for R_, s_, t_ in fits:
        res_ = np.linalg.norm((R_ @ (V0 * s_).T).T + t_ - V, axis=1)
        if best is None or (res_ > 5e-5).sum() < (best[3] > 5e-5).sum():
            best = (R_, s_, t_, res_)
    R, s, t, res = best
    sculpted = res > 5e-5
    print("FIT", name, "scale %.4f" % s, "rot %.2f deg" % np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))), "max sculpt %.2f mm" % (res.max() * 1000))
    me.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(me.loops))
    auto = np.array([tuple(c.vector) for c in me.corner_normals])
    keep = (R @ N0.T).T
    loop_new = np.zeros(len(me.loops), bool)
    for p in me.polygons:
        if sculpted[list(p.vertices)].any():
            loop_new[p.loop_start:p.loop_start + p.loop_total] = True
    final = np.where(loop_new[:, None], auto, keep)
    me.normals_split_custom_set([tuple(n) for n in final])
    names = [u.name for u in me.uv_layers]
    for nm_ in names[1:]:
        me.uv_layers.remove(me.uv_layers[nm_])
    me.uv_layers[0].name = "UVMap"
    print("PART", part, "verts", len(V), "sculpted verts", int(sculpted.sum()), "recomputed loops", int(loop_new.sum()),
          "rigid move mm", np.round((V.mean(0) - V0.mean(0)) * 1000, 2), "mats", [m.name for m in me.materials])

    item = o.copy(); item.data = me.copy(); bpy.context.scene.collection.objects.link(item)
    o.name = part
    skin(o, arm)
    export(os.path.join(W, "fbx", part + ".fbx"), [arm, o], arm, {'ARMATURE', 'MESH', 'EMPTY'})
    item.data.transform(Matrix.Translation(Vector(ITEM_SHIFT))); item.name = part
    h = box(item, "UCX_Item") if part in BOX_ITEM else ucx(item, "UCX_Item")
    export(os.path.join(W, "fbx", part + "_Item.fbx"), [item, h], item, {'MESH'})
    bpy.data.objects.remove(item, do_unlink=True); bpy.data.objects.remove(h, do_unlink=True)
    bpy.data.objects.remove(o, do_unlink=True)
print("DONE")
