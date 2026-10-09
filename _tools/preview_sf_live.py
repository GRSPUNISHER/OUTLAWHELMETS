"""SF V2 helmet (core + shells + rails) in one colour with every attachment, loaded into a NEW scene of the running
Blender (MCP exec), so nothing already open is touched. Worn FBXs share the user's SF .blend frame; materials resolve
xob.meta -> emat -> BCR/NMO (DirectX normal, AO from NMO alpha). One collection per helmet slot; the first item of a
slot is shown, alternatives are in the same collection, hidden. Head (Body_LOD0) appended from the user's SF .blend.

  exec(open(r"...\\_tools\\preview_sf_live.py").read())     # CODE / SLOTS can be preset in globals
"""
import bpy, os, re

TOOLS = r"C:/Users/lebea/Documents/Github/OUTLAWHELMETS/_tools/"
ADDON = r"C:/Users/lebea/Documents/Github/OUTLAWHELMETS/SFHELMETS/"
SF_BLEND = "C:/Users/lebea/OneDrive/Desktop/hELMET PROJECT/Fast SF v2 BUMP AND BALLISTIC HELMET.blend"
CODE = globals().get("CODE", "RG")
ACC = "ASSETS/Helmet Accessories/"
H = f"ASSETS/HELMET {CODE}/"
SLOTS = globals().get("SLOTS") or [
    ("Core", [("SF V2 Core (MCB, shared)", "ASSETS/HELMET BLACK/SF V2 Core.fbx")]),
    ("Shell", [("SF V2 Ballistic Shell (RG)", H + "SF V2 Ballistic Shell.fbx"), ("SF V2 Bump Shell (RG)", H + "SF V2 Bump Shell.fbx")]),
    ("Rails", [("SF V2 Rails (RG)", H + "SF V2 Rails.fbx")]),
    ("Earpro", [("Comtac VII (RG)", ACC + "COMTACS/RG COMTACS/comtacviinostrap.fbx"),
                ("Ops-Core AMP (RG)", ACC + "AMP/RG AMP/OpsCore_AMP.fbx"),
                ("Comtac VI", ACC + "COMTACS/COMTAC VI/comtacvi.fbx")]),
    ("BRS", [("PVS-31 BRS (OD)", ACC + "BATTERYPACK/OD BRS/batterypack.fbx")]),
    ("Battery", [("ShawBrain Pouch (RG)", ACC + "ShawBrainPouch/RG SHAWBRAIN/shawbrainpouch.fbx"),
                 ("BNVD Battery Pack", ACC + "BNVD BATTERY/bnvdbattery.fbx")]),
    ("Counterweight", [("Ops-Core Counterweight (RG)", ACC + "COUNTERWEIGHT/RG COUNTERWEIGHT/counterweight.fbx")]),
    ("Scrims", [("HighCut Oak Scrim (RG)", ACC + "Scrims/HighCut Ranger Green/HighCut Scrim Oak.fbx"),
                ("HighCut SemiCircle Scrim (RG)", ACC + "Scrims/HighCut Semi RG/HighCut Scrim Oak.fbx")]),
]
SCENE = globals().get("SCENE_NAME", f"SF V2 {CODE}")


def res_path(r):
    return ADDON + re.sub(r"^\{[0-9A-F]{16}\}", "", r)


def find_img(stem):
    for ext in (".png", ".tif", ".tiff", ".tga", ".dds"):
        if os.path.exists(stem + ext):
            return stem + ext
    return None


def maps(fbx_rel, src_mat):
    meta = ADDON + fbx_rel[:-4] + ".xob.meta"
    if not os.path.exists(meta):
        return None
    t = open(meta, encoding="utf-8").read()
    m = re.search(r'SourceMaterial "%s"\s*AssignedMaterial "([^"]+)"' % re.escape(src_mat), t)
    if not m or not os.path.exists(res_path(m.group(1))):
        return None
    e = open(res_path(m.group(1)), encoding="utf-8").read()
    out = {"emat": os.path.basename(res_path(m.group(1)))}
    for k in ("BCRMap", "NMOMap"):
        b = re.search(k + r' "([^"]+)"', e)
        if b:
            out[k] = find_img(res_path(b.group(1))[:-5])
    return out


def material(src, mp):
    key = f"{CODE}|{src}|{mp['emat'] if mp else 'none'}"
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.65
    if not mp:
        return mat
    L = nt.links
    if mp.get("BCRMap"):
        tb = nt.nodes.new("ShaderNodeTexImage")
        tb.image = bpy.data.images.load(mp["BCRMap"], check_existing=True)
        tb.image.alpha_mode = "CHANNEL_PACKED"
        L.new(tb.outputs["Alpha"], bsdf.inputs["Roughness"])
    if mp.get("NMOMap"):
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(mp["NMOMap"], check_existing=True)
        tn.image.colorspace_settings.name = "Non-Color"
        tn.image.alpha_mode = "CHANNEL_PACKED"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        comb = nt.nodes.new("ShaderNodeCombineColor"); comb.inputs[2].default_value = 1.0
        nm = nt.nodes.new("ShaderNodeNormalMap")
        L.new(tn.outputs["Color"], sep.inputs[0]); L.new(sep.outputs[0], comb.inputs[0])
        L.new(sep.outputs[1], inv.inputs[1]); L.new(inv.outputs[0], comb.inputs[1])
        L.new(comb.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], bsdf.inputs["Normal"])
        L.new(sep.outputs[2], bsdf.inputs["Metallic"])
    if mp.get("BCRMap"):
        if mp.get("NMOMap"):
            ao = nt.nodes.new("ShaderNodeMixRGB"); ao.blend_type = "MULTIPLY"; ao.inputs[0].default_value = 1.0
            L.new(tb.outputs["Color"], ao.inputs[1]); L.new(tn.outputs["Alpha"], ao.inputs[2])
            L.new(ao.outputs[0], bsdf.inputs["Base Color"])
        else:
            L.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


win = bpy.context.window_manager.windows[0]
scene = bpy.data.scenes.get(SCENE) or bpy.data.scenes.new(SCENE)
win.scene = scene
for c in list(scene.collection.children):
    for o in list(c.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(c)

missing = []
report = []
for slot, items in SLOTS:
    col = bpy.data.collections.new(f"{slot}")
    scene.collection.children.link(col)
    for i, (label, rel) in enumerate(items):
        if not os.path.exists(ADDON + rel):
            missing.append(f"{label}: FBX missing {rel}")
            continue
        before = set(bpy.data.objects)
        with bpy.context.temp_override(window=win, scene=scene):
            bpy.ops.import_scene.fbx(filepath=ADDON + rel)
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH" and not re.match(r"^(UTM|UCX|UBX|USP|UCS|UCL)", o.name)]
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            for md in [m for m in o.modifiers if m.type == "ARMATURE"]:
                o.modifiers.remove(md)
            for s in o.material_slots:
                if s.material:
                    src = re.sub(r"\.\d{3}$", "", s.material.name)
                    mp = maps(rel, src)
                    if not mp or not mp.get("BCRMap"):
                        missing.append(f"{label}: {src}")
                    s.material = material(src, mp)
            for c in o.users_collection:
                c.objects.unlink(o)
            col.objects.link(o)
            o.name = label if len(meshes) == 1 else f"{label} - {o.name}"
        for o in new:
            if o not in meshes:
                bpy.data.objects.remove(o, do_unlink=True)
        report.append((slot, label, len(meshes), "shown" if i == 0 else "hidden"))
        for o in meshes:
            o.hide_set(i > 0)
            o.hide_render = i > 0

head = bpy.data.collections.new("Head (reference)")
scene.collection.children.link(head)
with bpy.data.libraries.load(SF_BLEND, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n == "Body_LOD0"]
for o in dst.objects:
    if o is None:
        continue
    head.objects.link(o)
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
    for md in [m for m in o.modifiers if m.type == "ARMATURE"]:
        o.modifiers.remove(md)

for r in report:
    print(r)
print("MISSING", missing)
