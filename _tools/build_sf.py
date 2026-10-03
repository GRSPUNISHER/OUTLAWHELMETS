"""Export the modular SF V2 helmet parts + attachments from the user's placed .blend (Blender 4.5, headless).

  blender -b "<Fast SF v2 BUMP AND BALLISTIC HELMET.blend>" --python _tools/build_sf.py

The .blend is already in the OUTLAW export frame (forward +Y, Head bone head (0,-0.032,1.618)), and every
attachment sits where the user placed it: parts are exported RIGID, positions untouched.
Writes _tools/work/fbx/<Part>.fbx (skinned 100% to Head, OUTLAW armature) and <Part>_Item.fbx (dropped model,
unskinned, shifted by ITEM_SHIFT, UCX_Item hull) + _tools/work/parts.json.
"""
import bpy, bmesh, os, re, json
import numpy as np
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TOOLS, "work", "fbx")
TEMPLATE = os.path.join(TOOLS, "template", "SF V2 Bump (Rigged).fbx")
ITEM_SHIFT = (0.0, 0.02, -1.70)
UCX_MAT = "plastic_5EAA7FB0A83F90CF"

# part -> (source objects, material rename map, UTM collider material or None)
PARTS = {
    "SF_Bump": (["Carbon"], {}, "armor_5mm_18C62B7F4A626E3B"),
    "SF_Ballistic": (["SF"], {}, "hard_aramid_CF50027087BA3402"),
    "SF_Rails": (["Rails"], {}, None),
    "SM_PVS31_BRS": (["SM_PVS31_BRS"], {}, None),
    "SM_PeltorComtac_VII_ARC": (["SM_PeltorComtac_VII_ARC"], {}, None),
    "High_Cut_Helmet_Scrim_Oak": (["High_Cut_Helmet_Scrim_Oak"], {}, None),
    "High_Cut_Helmet_Scrim_SemiCircle": (["High_Cut_Helmet_Scrim_SemiCircle"], {}, None),
    "OpsCore_AMP": (["EarPro_OpsCore_AMP_Mount_Base_L"], {"MI_Ops_Core_AMP_Headset": "MI_Ops_Core_AMP_Headset"}, None),
    "SM_Comtac_6_ARC": (["SM_Comtac_6_ARC"], {}, None),
    "NVG_Counterweight_OpsCore_Kit": (["NVG_Counterweight_OpsCore_Kit"], {}, None),
    "BNVDFBat": (["BNVDFBat"], {}, None),
}


def import_template():
    user_arm = bpy.data.objects["Armature"]
    user_arm.name = "UserArmature"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=TEMPLATE)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    for o in new:
        if o.type == 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    arm.name = "Armature"
    worst = 0.0
    for b in arm.data.bones:
        ub = user_arm.data.bones.get(b.name)
        if ub is None:
            raise SystemExit("bone missing in the .blend armature: " + b.name)
        A = arm.matrix_world @ b.matrix_local
        B = user_arm.matrix_world @ ub.matrix_local
        worst = max(worst, max(abs(A[i][j] - B[i][j]) for i in range(4) for j in range(4)))
    print("ARMATURE max bone matrix diff vs .blend armature: %.6f" % worst)
    return arm


def base_name(n):
    return re.sub(r"\.\d{3}$", "", n)


def make_copy(srcs, name, matmap):
    copies = []
    for s in srcs:
        o = bpy.data.objects[s]
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        c = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(c)
        copies.append(c)
    c = copies[0]
    if len(copies) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for x in copies:
            x.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.object.join()
    me = c.data
    for i, m in enumerate(me.materials):
        b = base_name(m.name)
        for k, v in matmap.items():
            if b.startswith(k):
                b = v
        tgt = bpy.data.materials.get(b) or bpy.data.materials.new(b)
        me.materials[i] = tgt
    names = [m.name for m in me.materials]
    uniq = list(dict.fromkeys(names))
    idx = [uniq.index(names[p.material_index]) for p in me.polygons]
    used = sorted(set(idx))
    me.materials.clear()
    for u in used:
        me.materials.append(bpy.data.materials[uniq[u]])
    for p, i in zip(me.polygons, idx):
        p.material_index = used.index(i)
    if me.uv_layers and me.uv_layers[0].name != "UVMap":
        me.uv_layers[0].name = "UVMap"
    for uv in list(me.uv_layers)[1:]:
        me.uv_layers.remove(uv)
    c.name = name
    me.name = name
    return c


def skin(o, arm):
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name="Head")
    g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    mw = o.matrix_world.copy()
    o.parent = arm
    o.parent_type = 'OBJECT'
    o.matrix_world = mw
    o.modifiers.new("Armature", 'ARMATURE').object = arm


def utm_of(shell, matname):
    me = shell.data.copy()
    u = bpy.data.objects.new("UTM_Helmet", me)
    bpy.context.scene.collection.objects.link(u)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(me); bm.free()
    d = u.modifiers.new("dec", 'DECIMATE')
    d.ratio = min(1.0, 2400.0 / max(1, len(me.polygons)))
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(u.evaluated_get(dg))
    u.modifiers.clear()
    u.data = me2
    me2.materials.clear()
    me2.materials.append(bpy.data.materials.get(matname) or bpy.data.materials.new(matname))
    for uv in list(me2.uv_layers):
        me2.uv_layers.remove(uv)
    print("  UTM faces", len(me2.polygons))
    return u


BOX_ITEM = {"NVG_Counterweight_OpsCore_Kit", "BNVDFBat"}   # 64-point hulls of these small parts had degenerate faces


def box(objs, name):
    pts = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in objs])
    lo, hi = pts.min(0), pts.max(0)
    bm = bmesh.new()
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            for z in (lo[2], hi[2]):
                bm.verts.new((x, y, z))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(bpy.data.materials.get(UCX_MAT) or bpy.data.materials.new(UCX_MAT))
    return o


def hull(objs, name, max_points=64):
    pts = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in objs])
    bm0 = bmesh.new()
    for p in pts:
        bm0.verts.new(p)
    bmesh.ops.convex_hull(bm0, input=bm0.verts)
    hv = np.array([tuple(v.co) for v in bm0.verts if v.link_faces]); bm0.free()
    idx = [int(np.argmax(np.linalg.norm(hv - hv.mean(0), axis=1)))]
    d = np.linalg.norm(hv - hv[idx[0]], axis=1)
    for _ in range(min(max_points, len(hv)) - 1):
        i = int(np.argmax(d)); idx.append(i)
        d = np.minimum(d, np.linalg.norm(hv - hv[i], axis=1))
    bm = bmesh.new()
    for p in hv[idx]:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(bpy.data.materials.get(UCX_MAT) or bpy.data.materials.new(UCX_MAT))
    return o


def select_only(objs, active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = active


def export(path, objs, active, types):
    select_only(objs, active)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types=types, add_leaf_bones=False,
                             bake_anim=False, use_armature_deform_only=False, mesh_smooth_type='FACE',
                             apply_unit_scale=True, use_space_transform=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    arm = import_template()
    info = {}
    only = set(filter(None, os.environ.get("ONLY", "").split(",")))
    for part, (srcs, matmap, utm) in PARTS.items():
        if only and part not in only:
            continue
        print("PART", part)
        m = make_copy(srcs, part, matmap)
        ws = np.array([tuple(v.co) for v in m.data.vertices])
        worn = [m]
        skin(m, arm)
        if utm:
            u = utm_of(m, utm)
            u.matrix_world = Matrix.Identity(4)
            skin(u, arm)
            worn.append(u)
        export(os.path.join(OUT, part + ".fbx"), [arm] + worn, arm, {'ARMATURE', 'MESH', 'EMPTY'})
        for o in worn:
            bpy.data.objects.remove(o, do_unlink=True)
        item = make_copy(srcs, part, matmap)
        item.data.transform(Matrix.Translation(Vector(ITEM_SHIFT)))
        ucx = box([item], "UCX_Item") if part in BOX_ITEM else hull([item], "UCX_Item")
        export(os.path.join(OUT, part + "_Item.fbx"), [item, ucx], item, {'MESH'})
        info[part] = {"mats": [mt.name for mt in item.data.materials], "verts": len(ws),
                      "bbmin": ws.min(0).round(4).tolist(), "bbmax": ws.max(0).round(4).tolist(), "utm": utm}
        bpy.data.objects.remove(item, do_unlink=True)
        bpy.data.objects.remove(ucx, do_unlink=True)
        print("  mats", info[part]["mats"], "bb", info[part]["bbmin"], info[part]["bbmax"])
    if not only:
        json.dump(info, open(os.path.join(TOOLS, "work", "parts.json"), "w"), indent=1)


main()
