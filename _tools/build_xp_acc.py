"""XP-only attachments from the user's fit (Blender 4.5 headless):

  blender -b --python _tools/build_xp_acc.py

User 2026-09-30 re-placed / scaled / sculpted every attachment except the BNVD battery on the FAST XP helmets in
_tools/work/xp/XP_all_attachments_AOR1.blend (saved copy: ..._userfix.blend; my untouched build: ..._orig.blend; one fit
for XP3 / XP4 / XPC3 / XPC4). They become separate "(XP)" items; the SF / Maritime keep theirs. Same export as
build_maritime_acc.py: the user's world-space geometry as-is (skinned to Head, OUTLAW template armature) plus an _Item
model (ITEM_SHIFT + UCX_Item hull; a box for the ShawBrain).

Normals: the user used object scale as well as sculpting, so each part is fitted with the best of identity / rigid /
similarity / the object-matrix change / a trimmed affine; vendor custom normals follow that fit (inverse transpose).
Vertices off the fit (sculpted) get the vendor normal turned by the local rotation of the surface (welded area-weighted
normal of the fitted mesh -> of the user's mesh), which keeps the vendor's hard and soft edges.
Writes _tools/work/xp/fbx/XP_<part>.fbx / _Item.fbx and _tools/work/xp/acc_report.json.
"""
import os
_T = os.path.dirname(os.path.abspath(__file__))
_s = open(os.path.join(_T, "build_maritime.py"), encoding="utf-8").read()
exec(_s[_s.index("import bpy"):_s.index("def main():")])
_a = open(os.path.join(_T, "build_maritime_acc.py"), encoding="utf-8").read()
exec(_a[_a.index("def box(obj, name):"):_a.index("def snapshot(path):")])

W = os.path.join(TOOLS, "work", "xp")
PARTS = {"Ops-Core AMP": "XP_AMP", "Comtac VII (RG)": "XP_Comtac7", "Comtac VI": "XP_Comtac6", "PVS-31 BRS": "XP_BRS",
         "ShawBrain Pouch (MC)": "XP_ShawBrain", "Ops-Core Counterweight": "XP_Counterweight",
         "HighCut Oak Scrim (MC)": "XP_ScrimOak", "HighCut SemiCircle Scrim (MC)": "XP_ScrimSemi"}
BOX_ITEM = {"XP_ShawBrain"}
TOL = 5e-5


def hull_ok(h, area=3e-5, alt=0.001):
    for p in h.data.polygons:
        e = max((h.data.vertices[a].co - h.data.vertices[b].co).length for a, b in p.edge_keys)
        if p.area < area or 2 * p.area / e < alt:
            return False
    return True


def safe_ucx(obj, name):
    """ucx(); Workbench rejects a hull with sliver faces ("Face is degenerated" -> "Collider is not valid"), so a hull whose
    smallest face is under 0.3 cm2 is rebuilt from fewer farthest-point samples until every face is a sound triangle."""
    h = ucx(obj, name)
    if min(p.area for p in h.data.polygons) >= 3e-5:
        return h
    pts = np.array([tuple(obj.matrix_world @ v.co) for v in obj.data.vertices])
    for n in (40, 28, 20, 14, 10):
        bpy.data.objects.remove(h, do_unlink=True)
        idx = [int(np.argmax(np.linalg.norm(pts - pts.mean(0), axis=1)))]
        dd = np.linalg.norm(pts - pts[idx[0]], axis=1)
        for _ in range(n - 1):
            i = int(np.argmax(dd)); idx.append(i); dd = np.minimum(dd, np.linalg.norm(pts - pts[i], axis=1))
        bm = bmesh.new()
        for p in pts[idx]:
            bm.verts.new(p)
        bmesh.ops.convex_hull(bm, input=bm.verts)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        h = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(h)
        me.materials.append(bpy.data.materials.get(UCX_MAT) or bpy.data.materials.new(UCX_MAT))
        if hull_ok(h):
            return h
    bpy.data.objects.remove(h, do_unlink=True)
    return box(obj, name)


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {}
    for n in PARTS:
        o = bpy.data.objects[n]
        M = np.array(o.matrix_world)
        V = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        N = np.array([tuple(c.vector) for c in o.data.corner_normals]) @ np.linalg.inv(M[:3, :3])
        N /= np.linalg.norm(N, axis=1, keepdims=True)
        out[n] = (V, N, M, np.array([l.vertex_index for l in o.data.loops]))
    return out


def affine_fit(A, B):
    X = np.hstack([A, np.ones((len(A), 1))])
    S, *_ = np.linalg.lstsq(X, B, rcond=None)
    return S[:3].T, S[3]


def candidates(V0, V, M0, M1):
    out = [("identity", np.eye(3), np.zeros(3))]
    R, t = kabsch(V0, V); out.append(("rigid", R, t))
    c0, c1 = V0.mean(0), V.mean(0); s = np.sqrt(((V - c1) ** 2).sum() / ((V0 - c0) ** 2).sum())
    R, t = kabsch(V0 * s, V); out.append(("similarity", R * s, t))
    D = M1 @ np.linalg.inv(M0); out.append(("object matrix", D[:3, :3], D[:3, 3]))
    keep = np.ones(len(V0), bool)
    for _ in range(12):
        if keep.sum() < 12:
            break
        L, t = affine_fit(V0[keep], V[keep])
        res = np.linalg.norm(V0 @ L.T + t - V, axis=1)
        new = res < max(TOL, np.percentile(res, 60))
        if (new == keep).all():
            break
        keep = new
    if keep.sum() >= 12:
        out.append(("trimmed affine", L, t))
    return out


def face_normals(P, polys):
    out = np.zeros((len(polys), 3))
    for i, idx in enumerate(polys):
        q = P[idx]
        out[i] = np.cross(q, np.roll(q, -1, axis=0)).sum(0) * 0.5
    return out


def rotate(n, a, b):
    """n turned by the smallest rotation that takes unit a to unit b (rowwise)."""
    v = np.cross(a, b); c = (a * b).sum(1, keepdims=True)
    ok = c[:, 0] > -0.99
    r = n * c + np.cross(v, n) + v * (v * n).sum(1, keepdims=True) / np.where(ok[:, None], 1 + c, 1)
    return np.where(ok[:, None], r, n)


orig = snapshot(os.path.join(W, "XP_all_attachments_AOR1_orig.blend"))
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, "XP_all_attachments_AOR1_userfix.blend"))
mats_world = {n: np.array(bpy.data.objects[n].matrix_world) for n in PARTS}
for o in list(bpy.data.objects):
    if o.name not in PARTS:
        bpy.data.objects.remove(o, do_unlink=True)
arm = import_template()
os.makedirs(os.path.join(W, "fbx"), exist_ok=True)
report = {}
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
    V0, N0, M0, L0 = orig[name]
    loop_v = np.array([l.vertex_index for l in me.loops])
    if len(V) != len(V0) or len(loop_v) != len(L0) or (loop_v != L0).any():
        raise SystemExit(f"{name}: topology changed, cannot carry the vendor normals")
    best = None
    for label, L, t in candidates(V0, V, M0, mats_world[name]):
        res = np.linalg.norm(V0 @ L.T + t - V, axis=1)
        if best is None or (res > TOL).sum() < (best[3] > TOL).sum():
            best = (label, L, t, res)
    label, L, t, res = best
    sculpted = res > TOL
    P = V0 @ L.T + t
    Np = N0 @ np.linalg.inv(L)
    Np /= np.linalg.norm(Np, axis=1, keepdims=True)
    polys = [np.array(p.vertices) for p in me.polygons]
    fp, fa = face_normals(P, polys), face_normals(V, polys)
    weld = {}
    wid = np.array([weld.setdefault(tuple(k), len(weld)) for k in np.round(V0, 5)])
    gp, ga = np.zeros((len(weld), 3)), np.zeros((len(weld), 3))
    for i, idx in enumerate(polys):
        np.add.at(gp, wid[idx], fp[i]); np.add.at(ga, wid[idx], fa[i])
    lp, la = np.linalg.norm(gp, axis=1, keepdims=True), np.linalg.norm(ga, axis=1, keepdims=True)
    usable = ((lp > 1e-12) & (la > 1e-12))[:, 0]
    a = gp / np.where(lp > 1e-12, lp, 1); b = ga / np.where(la > 1e-12, la, 1)
    turn = sculpted[loop_v] & usable[wid[loop_v]]
    final = np.where(turn[:, None], rotate(Np, a[wid[loop_v]], b[wid[loop_v]]), Np)
    final /= np.linalg.norm(final, axis=1, keepdims=True)
    me.normals_split_custom_set([tuple(n) for n in final])
    ang = np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))[wid[loop_v]][turn]
    names = [u.name for u in me.uv_layers]
    for nm_ in names[1:]:
        me.uv_layers.remove(me.uv_layers[nm_])
    me.uv_layers[0].name = "UVMap"
    sv = np.linalg.svd(L, compute_uv=False)
    report[part] = {"source": name, "fit": label, "verts": len(V), "sculpted_verts": int(sculpted.sum()),
                    "max_sculpt_mm": round(float(res.max()) * 1000, 2), "fit_scale": [round(float(x), 4) for x in sv],
                    "centre_move_mm": [round(float(x) * 1000, 2) for x in V.mean(0) - V0.mean(0)],
                    "turned_loops": int(turn.sum()), "max_normal_turn_deg": round(float(ang.max()), 1) if len(ang) else 0.0,
                    "materials": [m.name for m in me.materials]}
    print("PART", part, report[part])

    item = o.copy(); item.data = me.copy(); bpy.context.scene.collection.objects.link(item)
    o.name = part
    skin(o, arm)
    export(os.path.join(W, "fbx", part + ".fbx"), [arm, o], arm, {'ARMATURE', 'MESH', 'EMPTY'})
    item.data.transform(Matrix.Translation(Vector(ITEM_SHIFT))); item.name = part
    h = box(item, "UCX_Item") if part in BOX_ITEM else safe_ucx(item, "UCX_Item")
    print("HULL", part, len(h.data.vertices), len(h.data.polygons), "min face area %.3g" % min(p.area for p in h.data.polygons))
    export(os.path.join(W, "fbx", part + "_Item.fbx"), [item, h], item, {'MESH'})
    bpy.data.objects.remove(item, do_unlink=True); bpy.data.objects.remove(h, do_unlink=True)
    bpy.data.objects.remove(o, do_unlink=True)
json.dump(report, open(os.path.join(W, "acc_report.json"), "w"), indent=1)
print("DONE")
