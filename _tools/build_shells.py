"""Split every OUTLAW helmet into a core + an interchangeable shell (Blender 4.5 headless:  blender -b --python _tools/build_shells.py).

User 2026-09-30: "do the interchangeable shells for all the helmets". Within each family the harness / chin strap / liner /
pads are the SAME geometry for every shell (the user's SF .blend joins the same Base into Carbon and SF; the Maritime and XP
harness vertices were snapped onto the SF harness), so each family gets ONE core and one shell part per helmet type:
  core  = the islands inside the outer shell / below its rim that are the SAME piece (2 mm) in every shell of the family
          (harness, chin strap, shared pads) - so one core fits every shell exactly,
  shell = everything else: the outer shell, every island sitting on it (shroud, loop panels, rail bases, 4-hole plate)
          and the shell-specific inside parts (the inner liner skin differs between XP / Carbon and Bump / Ballistic).
Per vertex: ray from the head centre through the vertex; if it meets the outer shell (largest island by area) before the
vertex, the vertex is outside. An island is "on the shell" when most of its vertices are outside.
Inputs = the worn FBXs the helmets are built from; outputs _tools/work/shells/fbx/<Fam>_Core(.fbx|_Item.fbx) and
<Type>_ShellOnly(.fbx|_Item.fbx) (worn: skinned to Head, UTM_Helmet hit zone on the SHELL only; item: ITEM_SHIFT + UCX_Item),
plus _tools/work/shells/report.json and check renders.
"""
import os, json
_T = os.path.dirname(os.path.abspath(__file__))
_s = open(os.path.join(_T, "build_maritime.py"), encoding="utf-8").read()
exec(_s[_s.index("import bpy"):_s.index("def main():")])
_a = open(os.path.join(_T, "build_maritime_acc.py"), encoding="utf-8").read()
exec(_a[_a.index("def box(obj, name):"):_a.index("def snapshot(path):")])
_x = open(os.path.join(_T, "build_xp_acc.py"), encoding="utf-8").read()
exec(_x[_x.index("def hull_ok("):_x.index("def snapshot(path):\n    bpy.ops.wm.open_mainfile")])
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

W = os.path.join(TOOLS, "work")
OUTD = os.path.join(W, "shells", "fbx")
C = Vector((0.0, -0.01, 1.66))
GM_BUMP = "armor_5mm_18C62B7F4A626E3B"
GM_BAL = "hard_aramid_CF50027087BA3402"
FAMILIES = {
    "SF": ("SF_Bump", {"SF_Bump": ("fbx/SF_Bump.fbx", GM_BUMP), "SF_Ballistic": ("fbx/SF_Ballistic.fbx", GM_BAL)}),
    "MT": ("MT", {"MT": ("maritime/fbx/MT_Shell.fbx", GM_BAL)}),
    "XP": ("XP3", {"XP3": ("xp/fbx/XP3_Shell.fbx", GM_BAL), "XP4": ("xp/fbx/XP4_Shell.fbx", GM_BAL),
                   "XPC3": ("xp/fbx/XPC3_Shell.fbx", GM_BAL), "XPC4": ("xp/fbx/XPC4_Shell.fbx", GM_BAL)}),
}


def load_world(path, name):
    b = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in b]
    mesh = next(o for o in new if o.type == "MESH" and not o.name.startswith(("UTM", "UCX")))
    mw = mesh.matrix_world.copy()
    mesh.parent = None
    mesh.data.transform(mw)
    mesh.matrix_world = Matrix.Identity(4)
    mesh.modifiers.clear(); mesh.vertex_groups.clear()
    for o in new:
        if o is not mesh:
            bpy.data.objects.remove(o, do_unlink=True)
    for i, m in enumerate(mesh.data.materials):
        base = m.name.split(".")[0]
        mesh.data.materials[i] = bpy.data.materials.get(base) or bpy.data.materials.new(base)
    mesh.name = name
    return mesh


def classify(o):
    me = o.data
    isl = islands(o)
    comp = np.zeros(len(me.vertices), int)
    for k, g in enumerate(isl):
        comp[g] = k
    area = np.zeros(len(isl))
    for p in me.polygons:
        area[comp[p.vertices[0]]] += p.area
    shell = int(np.argmax(area))
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.verts[0].index] != shell], context='FACES')
    tree = BVHTree.FromBMesh(bm); bm.free()
    V = np.array([tuple(v.co) for v in me.vertices])
    outside = np.zeros(len(V), bool)
    for i, p in enumerate(V):
        d = Vector(p) - C
        L = d.length
        hit = tree.ray_cast(C, d.normalized(), L)
        outside[i] = hit[0] is not None and (hit[0] - C).length < L - 0.0005
    shell_isl = {shell} | {k for k, g in enumerate(isl) if k != shell and outside[g].mean() >= 0.5}
    return isl, comp, shell_isl


def part(o, keep_verts, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c)
    keep = set(keep_verts)
    bm = bmesh.new(); bm.from_mesh(c.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    bm.to_mesh(c.data); bm.free()
    me = c.data
    used = sorted({p.material_index for p in me.polygons})
    mats = [me.materials[i] for i in used]
    remap = {u: j for j, u in enumerate(used)}
    idx = [remap[p.material_index] for p in me.polygons]
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    for p, i in zip(me.polygons, idx):
        p.material_index = i
    return c


def outer_island(src):
    """The outer shell alone (largest island by area) - the protective surface the hit zone should be."""
    c = src.copy(); c.data = src.data.copy(); bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.faces.ensure_lookup_table()
    seen, best, best_a = set(), None, -1.0
    for f in bm.faces:
        if f.index in seen:
            continue
        st, g = [f], []
        seen.add(f.index)
        while st:
            x = st.pop(); g.append(x.index)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen:
                        seen.add(y.index); st.append(y)
        a = sum(bm.faces[i].calc_area() for i in g)
        if a > best_a:
            best, best_a = set(g), a
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in best], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(c.data); bm.free()
    return c


def utm_named(src, matname):
    """Hit zone of a shell, from the OUTER SHELL ONLY. Workbench silently dropped the SF Ballistic shell's UTM when it was
    decimated from the whole shell part (liner skin, pads, hardware): "Build successful", no GeometryParam, no collider, no
    warning. Isolated in Workbench: the Ballistic shell mesh took the Bump UTM fine, the Bump mesh lost the Ballistic UTM,
    and an outer-shell-only UTM imported. Then merge vertices, dissolve degenerate geometry and triangulate."""
    shell = outer_island(src)
    u = utm_of(shell)
    bpy.data.objects.remove(shell, do_unlink=True)
    bm = bmesh.new(); bm.from_mesh(u.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0005)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-8], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(u.data); bm.free()
    u.data.materials.clear()
    u.data.materials.append(bpy.data.materials.get(matname) or bpy.data.materials.new(matname))
    return u


def export_pair(obj, arm, name, utm_mat):
    item = obj.copy(); item.data = obj.data.copy(); bpy.context.scene.collection.objects.link(item)
    obj.name = name
    obj.data.name = name
    worn = [obj]; skin(obj, arm)
    if utm_mat:
        u = utm_named(obj, utm_mat); u.matrix_world = Matrix.Identity(4); skin(u, arm); worn.append(u)
        u.name = "UTM_Helmet"; u.data.name = "UTM_Helmet"
    export(os.path.join(OUTD, name + ".fbx"), [arm] + worn, arm, {'ARMATURE', 'MESH', 'EMPTY'})
    for x in worn:
        bpy.data.objects.remove(x, do_unlink=True)
    item.data.transform(Matrix.Translation(Vector(ITEM_SHIFT))); item.name = name
    h = safe_ucx(item, "UCX_Item")
    export(os.path.join(OUTD, name + "_Item.fbx"), [item, h], item, {'MESH'})
    bpy.data.objects.remove(item, do_unlink=True); bpy.data.objects.remove(h, do_unlink=True)


def vkey(V):
    return set(map(tuple, np.round(V, 3)))


MATCH_TOL = 0.002


def same_island(Va, ga, Vb, gb):
    """Same piece in two shells: equal vertex count, centroid within 2 mm, every vertex within 2 mm of the other island."""
    if len(ga) != len(gb) or np.linalg.norm(Va[ga].mean(0) - Vb[gb].mean(0)) > MATCH_TOL:
        return False
    kd = KDTree(len(gb))
    for j, i in enumerate(gb):
        kd.insert(Vb[i], j)
    kd.balance()
    return max(kd.find(Vector(Va[i]))[2] for i in ga) < MATCH_TOL


bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(OUTD, exist_ok=True)
arm = import_template()
report = {}
previews = {}
for fam, (ref, types) in FAMILIES.items():
    loaded = {}
    for t, (rel, gm) in types.items():
        o = load_world(os.path.join(W, rel), t)
        isl, comp, shell_isl = classify(o)
        V = np.array([tuple(v.co) for v in o.data.vertices])
        loaded[t] = (o, isl, shell_isl, V)
    core_of = {t: set() for t in types}
    ro, risl, rshell, rV = loaded[ref]
    for k, g in enumerate(risl):
        if k in rshell:
            continue
        found = {}
        for t, (o, isl, shell_isl, V) in loaded.items():
            m = next((kk for kk, gg in enumerate(isl) if kk not in shell_isl and same_island(rV, g, V, gg)), None)
            if m is None:
                break
            found[t] = m
        if len(found) == len(loaded):
            for t, m in found.items():
                core_of[t].add(m)
    cores = {}
    for t, (rel, gm) in types.items():
        o, isl, shell_isl, V = loaded[t]
        core_k = core_of[t]
        core_v = [v for k in core_k for v in isl[k]]
        shell_v = [v for k, g in enumerate(isl) if k not in core_k for v in g]
        cores[t] = V[core_v]
        s = part(o, shell_v, t + "_ShellOnly")
        pv = s.copy(); pv.data = s.data.copy(); pv.name = t + "_ShellOnly_preview"; bpy.context.scene.collection.objects.link(pv)
        previews[t] = pv
        report[t] = {"family": fam, "verts": len(V), "islands": len(isl), "outside_islands": len(shell_isl),
                     "core_islands": len(core_k), "shell_verts": len(shell_v), "core_verts": len(core_v),
                     "shell_mats": [m.name for m in s.data.materials]}
        export_pair(s, arm, t + "_ShellOnly", gm)
        if t == ref:
            c = part(o, core_v, fam + "_Core")
            pc = c.copy(); pc.data = c.data.copy(); pc.name = fam + "_Core_preview"; bpy.context.scene.collection.objects.link(pc)
            previews[fam + "_Core"] = pc
            report[fam + "_Core"] = {"verts": len(core_v), "mats": [m.name for m in c.data.materials]}
            export_pair(c, arm, fam + "_Core", None)
        bpy.data.objects.remove(o, do_unlink=True)
        print("TYPE", t, report[t])
    rk = vkey(cores[ref])
    for t, cv in cores.items():
        k = vkey(cv)
        report[t]["core_vs_" + ref] = {"only_here": len(k - rk), "only_in_ref": len(rk - k)}
        print("CORE CHECK", t, "vs", ref, report[t]["core_vs_" + ref])
json.dump(report, open(os.path.join(W, "shells", "report.json"), "w"), indent=1)

sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
sc.render.resolution_x = 360; sc.render.resolution_y = 360
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.40
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0.0, 1.66))
for o in previews.values():
    o.color = (0.85, 0.45, 0.2, 1) if "Core" in o.name else (0.55, 0.6, 0.65, 1)
combos = [("SF_Core",), ("SF_Core", "SF_Bump"), ("SF_Core", "SF_Ballistic"), ("MT_Core",), ("MT_Core", "MT"),
          ("XP_Core",), ("XP_Core", "XP3"), ("XP_Core", "XP4"), ("XP_Core", "XPC3"), ("XP_Core", "XPC4")]
for combo in combos:
    for o in previews.values():
        o.hide_render = not any(o.name == (k + "_preview" if "Core" in k else k + "_ShellOnly_preview") for k in combo)
    for vn, d in (("side", Vector((1, 0.2, 0.15))), ("front", Vector((0.3, 1, 0.1)))):
        cam.location = tgt + d.normalized() * 1.2
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(W, "shells", f"chk_{'+'.join(combo)}_{vn}.png")
        bpy.ops.render.render(write_still=True)
print("DONE")
