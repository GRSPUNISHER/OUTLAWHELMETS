"""Export the CRYE Airframe helmet + attachments for OUTLAWHELMETS (Blender 4.5 headless, run on the SF .blend for its body).

  blender -b "<Fast SF v2 BUMP AND BALLISTIC HELMET.blend>" --python _tools/build_airframe.py

Input: _tools/work/airframe/raw/<part>.fbx (airframe_extract.py, vendor frame, the user's placements). ONE rigid transform for
every part: Rz(180) + t from fit_airframe.json (fit_translate.py on the shell vs the Reforger head, SF gap targets), so the
attachments stay exactly where the .blend has them relative to the helmet. Writes worn (skinned to Head, OUTLAW armature) and
_Item (static, ITEM_SHIFT, UCX hull) FBXs to _tools/work/airframe/fbx/, plus a check render on the Reforger body.
"""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(TOOLS, "work", "airframe", "raw")
OUT = os.path.join(TOOLS, "work", "airframe", "fbx")
TEMPLATE = os.path.join(TOOLS, "template", "SF V2 Bump (Rigged).fbx")
ITEM_SHIFT = (0.0, 0.02, -1.70)
UCX_MAT = "plastic_5EAA7FB0A83F90CF"
PARTS = ["AF_Shell", "AF_Cover", "AF_ComtacVII", "AF_Helstar", "AF_TNVCLight", "AF_OpsCoreCounterweight", "AF_Mohawk", "AF_G24"]
UTM = {"AF_Shell": "hard_aramid_CF50027087BA3402"}
BOX_ITEM = {"AF_Helstar", "AF_OpsCoreCounterweight", "AF_TNVCLight", "AF_G24"}

# User: "air frame is way too big" -> uniform scale 0.91 solved with Shadows-Helmets fit_scale.py (sits higher, never clips);
# the SAME matrix goes on the shell and every accessory ("make sure the accessories are scaled too").
fit = json.load(open(os.path.join(TOOLS, "work", "airframe", "fit_airframe_scale.json")))
M = Matrix(fit["M"])


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
    return arm


def load_part(part):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(RAW, part + ".fbx"))
    new = [o for o in bpy.data.objects if o not in before]
    o = next(x for x in new if x.type == 'MESH')
    for x in new:
        if x is not o:
            bpy.data.objects.remove(x, do_unlink=True)
    o.data.transform(M @ o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    me = o.data
    for uv in list(me.uv_layers)[1:]:
        me.uv_layers.remove(uv)
    if me.uv_layers:
        me.uv_layers[0].name = "UVMap"
    for i, m in enumerate(me.materials):
        base = m.name.split(".")[0]
        me.materials[i] = bpy.data.materials.get(base) or bpy.data.materials.new(base)
    o.name = part; me.name = part
    return o


def skin(o, arm):
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name="Head")
    g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    mw = o.matrix_world.copy()
    o.parent = arm; o.parent_type = 'OBJECT'; o.matrix_world = mw
    o.modifiers.new("Armature", 'ARMATURE').object = arm


def utm_of(src, matname):
    me = src.data.copy()
    u = bpy.data.objects.new("UTM_Helmet", me)
    bpy.context.scene.collection.objects.link(u)
    d = u.modifiers.new("dec", 'DECIMATE')
    d.ratio = min(1.0, 2400.0 / max(1, len(me.polygons)))
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(u.evaluated_get(dg))
    u.modifiers.clear(); u.data = me2
    me2.materials.clear(); me2.materials.append(bpy.data.materials.get(matname) or bpy.data.materials.new(matname))
    for uv in list(me2.uv_layers):
        me2.uv_layers.remove(uv)
    return u


def ucx(objs, name, box):
    pts = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in objs])
    bm = bmesh.new()
    if box:
        lo, hi = pts.min(0), pts.max(0)
        for x in (lo[0], hi[0]):
            for y in (lo[1], hi[1]):
                for z in (lo[2], hi[2]):
                    bm.verts.new((x, y, z))
    else:
        b0 = bmesh.new()
        for p in pts:
            b0.verts.new(p)
        bmesh.ops.convex_hull(b0, input=b0.verts)
        hv = np.array([tuple(v.co) for v in b0.verts if v.link_faces]); b0.free()
        idx = [int(np.argmax(np.linalg.norm(hv - hv.mean(0), axis=1)))]
        dd = np.linalg.norm(hv - hv[idx[0]], axis=1)
        for _ in range(min(64, len(hv)) - 1):
            i = int(np.argmax(dd)); idx.append(i); dd = np.minimum(dd, np.linalg.norm(hv - hv[i], axis=1))
        for p in hv[idx]:
            bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(bpy.data.materials.get(UCX_MAT) or bpy.data.materials.new(UCX_MAT))
    return o


def export(path, objs, active, types):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types=types, add_leaf_bones=False, bake_anim=False,
                             use_armature_deform_only=False, mesh_smooth_type='FACE', apply_unit_scale=True, use_space_transform=True)


def render_check(objs):
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = True
    bpy.data.objects["Body_LOD0"].hide_render = False
    for o in objs:
        o.hide_render = False
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'RANDOM'
    sc.render.resolution_x = 700; sc.render.resolution_y = 700
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.5
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    tgt = Vector((0, -0.01, 1.68))
    for nm, d in (("side", Vector((1, 0, 0))), ("front", Vector((0, 1, 0.15))), ("q", Vector((0.7, 0.6, 0.4))), ("back", Vector((-0.3, -1, 0.3)))):
        cam.location = tgt + d.normalized() * 1.2
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(TOOLS, "work", "airframe", "check_" + nm + ".png")
        bpy.ops.render.render(write_still=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    arm = import_template()
    info = {}
    placed = []
    for part in PARTS:
        m = load_part(part)
        V = np.array([tuple(v.co) for v in m.data.vertices])
        info[part] = {"mats": [x.name for x in m.data.materials], "bbmin": V.min(0).round(4).tolist(), "bbmax": V.max(0).round(4).tolist()}
        preview = m.copy(); preview.data = m.data.copy(); preview.name = part + "_preview"
        bpy.context.scene.collection.objects.link(preview); placed.append(preview)
        worn = [m]
        skin(m, arm)
        if part in UTM:
            u = utm_of(m, UTM[part]); u.matrix_world = Matrix.Identity(4); skin(u, arm); worn.append(u)
        export(os.path.join(OUT, part + ".fbx"), [arm] + worn, arm, {'ARMATURE', 'MESH', 'EMPTY'})
        for o in worn:
            bpy.data.objects.remove(o, do_unlink=True)
        item = load_part(part)
        item.data.transform(Matrix.Translation(Vector(ITEM_SHIFT)))
        hull = ucx([item], "UCX_Item", part in BOX_ITEM)
        export(os.path.join(OUT, part + "_Item.fbx"), [item, hull], item, {'MESH'})
        bpy.data.objects.remove(item, do_unlink=True); bpy.data.objects.remove(hull, do_unlink=True)
        print("PART", part, info[part])
    json.dump(info, open(os.path.join(TOOLS, "work", "airframe", "parts.json"), "w"), indent=1)
    render_check(placed)


main()
