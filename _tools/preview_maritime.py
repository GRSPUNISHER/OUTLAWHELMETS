"""Maritime helmet with every attachment, textured, for a look in Blender (Blender 4.5 headless, then open the .blend):

  blender -b --python _tools/preview_maritime.py  [-- <colour code, default AOR1>]

Imports the addon's worn FBXs (same frame as the user's SF .blend, which is where the attachments were placed), drops the
armatures / UTM / UCX, gives every material its in-game BCR (resolved xob.meta -> emat -> BCRMap), appends the head
(Body_LOD0) from the user's SF .blend, one collection per helmet slot. Slots that take one item at a time show the first
item; the alternatives are in the same collection, hidden. Saves _tools/work/maritime/Maritime_all_attachments.blend.
"""
import bpy, os, re, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(TOOLS, "..", "SFHELMETS") + "/"
SF_BLEND = "C:/Users/lebea/OneDrive/Desktop/hELMET PROJECT/Fast SF v2 BUMP AND BALLISTIC HELMET.blend"
CODE = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "AOR1"
ACC = "ASSETS/Helmet Accessories/"
MT = f"ASSETS/MARITIME/MARITIME {CODE}/"
SLOTS = [
    ("Helmet", [("Maritime shell", MT + "Maritime.fbx")]),
    ("Rails", [("Maritime rails", MT + "MaritimeRails.fbx")]),
    ("BRS", [("PVS-31 BRS", ACC + "BATTERYPACK/batterypack.fbx")]),
    ("Battery", [("BNVD Battery Pack", ACC + "BNVD BATTERY/bnvdbattery.fbx"),
                 ("ShawBrain Pouch (MC)", ACC + "ShawBrainPouch/MC SHAWBRAIN/shawbrainpouch.fbx")]),
    ("Counterweight", [("Ops-Core Counterweight", ACC + "COUNTERWEIGHT/counterweight.fbx")]),
    ("Earpro", [("Comtac VII (RG)", ACC + "COMTACS/RG COMTACS/comtacviinostrap.fbx"),
                ("Ops-Core AMP", ACC + "AMP/OpsCore_AMP.fbx"),
                ("Comtac VI", ACC + "COMTACS/COMTAC VI/comtacvi.fbx")]),
    ("Scrims", [("HighCut Oak Scrim (MC)", ACC + "Scrims/HighCut Oak MC/HighCut Scrim Oak.fbx"),
                ("HighCut SemiCircle Scrim (MC)", ACC + "Scrims/HighCut Semi MC/HighCut Scrim Oak.fbx")]),
]


def res_path(r):
    return ADDON + re.sub(r"^\{[0-9A-F]{16}\}", "", r)


def bcr_image(fbx_rel, src_mat):
    meta = ADDON + fbx_rel[:-4] + ".xob.meta"
    if not os.path.exists(meta):
        return None
    t = open(meta, encoding="utf-8").read()
    m = re.search(r'SourceMaterial "%s"\s*AssignedMaterial "([^"]+)"' % re.escape(src_mat), t)
    if not m or not os.path.exists(res_path(m.group(1))):
        return None
    b = re.search(r'BCRMap "([^"]+)"', open(res_path(m.group(1)), encoding="utf-8").read())
    if not b:
        return None
    stem = res_path(b.group(1))[:-5]
    for ext in (".png", ".tif", ".tiff", ".tga", ".dds"):
        if os.path.exists(stem + ext):
            return stem + ext
    return None


def textured(name, img_path):
    key = f"{name}|{img_path}"
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.65
    if img_path:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(img_path, check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
missing = []
for slot, items in SLOTS:
    col = bpy.data.collections.new(slot)
    scene.collection.children.link(col)
    for i, (label, rel) in enumerate(items):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=ADDON + rel)
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH" and not o.name.startswith(("UTM", "UCX"))]
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            for md in [m for m in o.modifiers if m.type == "ARMATURE"]:
                o.modifiers.remove(md)
            for s in o.material_slots:
                if s.material:
                    src = s.material.name.split(".")[0]
                    img = bcr_image(rel, src)
                    if not img:
                        missing.append(f"{label}: {src}")
                    s.material = textured(src, img)
            for c in o.users_collection:
                c.objects.unlink(o)
            col.objects.link(o)
            o.name = label if len(meshes) == 1 else f"{label} - {o.name}"
            o.hide_set(i > 0)
            o.hide_render = i > 0
        for o in new:
            if o not in meshes:
                bpy.data.objects.remove(o, do_unlink=True)

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

out = os.path.join(TOOLS, "work", "maritime", f"Maritime_all_attachments_{CODE}.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
print("MISSING TEXTURES", missing)
for c in scene.collection.children:
    print(c.name, [o.name for o in c.objects])
