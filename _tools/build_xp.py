"""Build the Ops-Core FAST XP / XP Carbon (3-hole and 4-hole) for OUTLAWHELMETS (Blender 4.5, run on the user's SF .blend).

  blender -b "<Fast SF v2 BUMP AND BALLISTIC HELMET.blend>" --python _tools/build_xp.py

Same recipe as build_maritime.py (its helpers are reused): the user's SF placement (UV-matched Kabsch of SF_V2 "SF" onto the
.blend) applied after the Shadows fast_survey "XP" alignment; every harness vertex takes the user's SF harness position (the SF
chin strap). XP rails (from XP 3 Hole) are one removable part shared by all four; the 4-hole mount faces go to their own
material XP4M (the vendor re-used one UV area for the 3-hole frame and the 4-hole plate). Writes _tools/work/xp/fbx + renders.
"""
import os
_T = os.path.dirname(os.path.abspath(__file__))
_s = open(os.path.join(_T, "build_maritime.py"), encoding="utf-8").read()
exec(_s[_s.index("import bpy"):_s.index("def main():")])
OUT = os.path.join(TOOLS, "work", "xp", "fbx")
OBJS = {"XP 3 Hole": "XP3", "XP 4 Hole": "XP4", "Carbon 3 Hole": "XPC3", "Carbon 4 Hole": "XPC4"}


def main():
    os.makedirs(OUT, exist_ok=True)
    user_sf = bpy.data.objects["SF"]
    U = np.array([tuple(user_sf.matrix_world @ v.co) for v in user_sf.data.vertices])
    sfv2 = imp(SRC + "SF_V2/SF_V2/Opscore SF-FTHS.fbx", "S_")
    xp = imp(SRC + "OpscoreXP_Carbon/OpscoreXP_Carbon/xp_carbon.fbx", "X_")
    src_shell = sfv2["SF"]
    uv_src = uv_of_verts(src_shell); uv_usr = {}
    for vi, uv in uv_of_verts(user_sf).items():
        uv_usr.setdefault(uv, vi)
    pairs = [(vi, uv_usr[uv]) for vi, uv in uv_src.items() if uv in uv_usr]
    A = verts(src_shell)[[p[0] for p in pairs]]; B = U[[p[1] for p in pairs]]
    R, t = kabsch(A, B)
    print("USER TRANSFORM rms %.5f" % np.sqrt((np.linalg.norm((R @ A.T).T + t - B, axis=1) ** 2).mean()))
    T_user = np.eye(4); T_user[:3, :3] = R; T_user[:3, 3] = t
    sv = json.load(open(SURVEY))["XP"]
    M_xp = np.eye(4); M_xp[:3, :3] = np.array(sv["R"]); M_xp[:3, 3] = np.array(sv["t"])
    base = sfv2["Base"]; BV = verts(base)
    base_to_user = {vi: uv_usr[uv] for vi, uv in uv_of_verts(base).items() if uv in uv_usr}
    harness_islands = [g for g in islands(base) if len(g) < 1000 and not (BV[g].mean(0)[1] < -0.09 and BV[g].mean(0)[2] > 0.74)]
    hv = np.array([BV[g].mean(0) for g in harness_islands]); hn = [len(g) for g in harness_islands]
    arm = import_template()
    rails_done = False
    report = {}
    for src_name, key in OBJS.items():
        o = xp[src_name]
        XV = (M_xp[:3, :3] @ verts(o).T).T + M_xp[:3, 3]
        new_pos = (T_user[:3, :3] @ XV.T).T + T_user[:3, 3]
        orig = new_pos.copy()
        isl = islands(o)
        harness, used = [], set()
        for g in isl:
            c = XV[g].mean(0); best = None
            for k, (hc, n) in enumerate(zip(hv, hn)):
                if k in used or abs(n - len(g)) > 2:
                    continue
                d = np.linalg.norm(hc - c)
                if d < 0.006 and (best is None or d < best[1]):
                    best = (k, d)
            if best is None:
                continue
            used.add(best[0]); harness.extend(g)
            bg = harness_islands[best[0]]
            kd = KDTree(len(bg))
            for j, bi in enumerate(bg):
                kd.insert(BV[bi], j)
            kd.balance()
            for vi in g:
                _, j, _ = kd.find(Vector(XV[vi]))
                if bg[j] in base_to_user:
                    new_pos[vi] = U[base_to_user[bg[j]]]
        moved = np.linalg.norm(new_pos[harness] - orig[harness], axis=1)
        for i, v in enumerate(o.data.vertices):
            v.co = Vector(new_pos[i])
        hs = set(harness)
        rails, rest = [], []
        for g in isl:
            c = XV[g].mean(0); n = len(g)
            is_rail = not (set(g) & hs) and ((n >= 1000 and abs(c[0]) > 0.06) or (70 <= n <= 76 and abs(c[0]) > 0.078))
            (rails if is_rail else rest).extend(g)
        shell, rail = split(o, [rest, rails], [key + "_Shell", key + "_Rails"])
        for obj in (shell, rail):
            me = obj.data
            names = [u.name for u in me.uv_layers]
            for nm_ in names[1:]:
                me.uv_layers.remove(me.uv_layers[nm_])
            if len(me.uv_layers):
                me.uv_layers[0].name = "UVMap"
            for i, m in enumerate(obj.data.materials):
                b = m.name.split(".")[0]
                obj.data.materials[i] = bpy.data.materials.get(b) or bpy.data.materials.new(b)
        if key in ("XP4", "XPC4"):
            SV = np.linalg.solve(T_user[:3, :3], (verts(shell) - T_user[:3, 3]).T).T
            mats = [m.name for m in shell.data.materials]
            xi = mats.index("XP1")
            m4 = bpy.data.materials.get("XP4M") or bpy.data.materials.new("XP4M")
            shell.data.materials.append(m4); mi = len(shell.data.materials) - 1
            big = set(max(islands(shell), key=len))
            nm = 0
            for p in shell.data.polygons:
                if p.material_index != xi or p.vertices[0] in big:
                    continue
                cs = SV[list(p.vertices)].mean(0)
                if cs[1] < -0.085 and cs[2] > 0.70 and abs(cs[0]) < 0.06:
                    p.material_index = mi; nm += 1
            print(key, "4-hole mount faces -> XP4M", nm)
        report[key] = {"harness_islands": len(used), "strap_max_move": float(moved.max()) if len(moved) else 0.0}
        print(key, "harness matched", len(used), "of", len(harness_islands), "max move %.4f" % report[key]["strap_max_move"])
        outs = [(key + "_Shell", shell, True)]
        if not rails_done:
            outs.append(("XP_Rails", rail, False)); rails_done = True
        else:
            bpy.data.objects.remove(rail, do_unlink=True)
        for part, ob, utm in outs:
            item = ob.copy(); item.data = ob.data.copy(); bpy.context.scene.collection.objects.link(item)
            prev = ob.copy(); prev.data = ob.data.copy(); prev.name = part + "_preview"; bpy.context.scene.collection.objects.link(prev)
            ob.name = part
            worn = [ob]; skin(ob, arm)
            if utm:
                u = utm_of(ob); u.matrix_world = Matrix.Identity(4); skin(u, arm); worn.append(u)
            export(os.path.join(OUT, part + ".fbx"), [arm] + worn, arm, {'ARMATURE', 'MESH', 'EMPTY'})
            for x in worn:
                bpy.data.objects.remove(x, do_unlink=True)
            item.data.transform(Matrix.Translation(Vector(ITEM_SHIFT))); item.name = part
            h = ucx(item, "UCX_Item")
            export(os.path.join(OUT, part + "_Item.fbx"), [item, h], item, {'MESH'})
            bpy.data.objects.remove(item, do_unlink=True); bpy.data.objects.remove(h, do_unlink=True)
            print("PART", part, [m.name for m in prev.data.materials], len(prev.data.vertices))
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = True
    bpy.data.objects["Body_LOD0"].hide_render = False
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.render.resolution_x = 500; sc.render.resolution_y = 500
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.42
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    tgt = Vector((0, 0.0, 1.64))
    for key in OBJS.values():
        objs = [bpy.data.objects[key + "_Shell_preview"], bpy.data.objects["XP_Rails_preview"]]
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name != "Body_LOD0":
                o.hide_render = o not in objs
        for view, d in (("front", Vector((0, 1, 0))), ("side", Vector((1, 0, 0)))):
            cam.location = tgt + d * 1.2
            cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(TOOLS, "work", "xp", f"check_{key}_{view}.png")
            bpy.ops.render.render(write_still=True)
    json.dump(report, open(os.path.join(TOOLS, "work", "xp", "build_report.json"), "w"), indent=1)


main()
