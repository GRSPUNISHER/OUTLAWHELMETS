"""Adds the Vanguard (Phaseline NVS) NVGs + strobes and OUTLAW's GPNVG-18 battery to the live SF preview scene made by
preview_sf_live.py. NVG / strobe worn models are in their slot's local frame -> placed with the SF helmet's NVG /
HelStroke LoadoutSlotInfo (PivotID Head, Offset, Angles) on the Head bone frame decoded from the SF Core .txo
(engine -> Blender = (x, z, y)). Materials: the prefab's WornMaterialsOverride (xob material order) else the xob.meta.
"""
import bpy, os, re, json, math
from mathutils import Matrix

OUT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/SFHELMETS/"
NVS = "C:/Users/lebea/Documents/Github/Phaseline/Phaseline-Night-Vision-Systems/"
SLOTS_JSON = globals().get("SLOTS_JSON")
SCENE = globals().get("SCENE_NAME", "SF V2 RG")
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
SLOT_MATS = json.load(open(SLOTS_JSON))
ITEMS = globals().get("ITEMS") or [
    ("NVG", "NVG", [("GPNVG-18 (Black)", NVS, "Prefabs/NVG/VNVS_GPNVG18_Black.et"),
                    ("GPNVG-18 (Tan)", NVS, "Prefabs/NVG/VNVS_GPNVG18_Tan.et"),
                    ("PVS-31 (Black)", NVS, "Prefabs/NVG/VNVS_PVS31_Black.et")]),
    ("Strobe", "HelStroke", [("MS-2000 (OD)", NVS, "Prefabs/Strobes/VNVS_MS2000_OD.et"),
                             ("Manta (OD)", NVS, "Prefabs/Strobes/VNVS_Manta_OD.et"),
                             ("IFF Beacon (OD)", NVS, "Prefabs/Strobes/VNVS_IFFBeacon_OD.et")]),
    ("Battery", None, [("GPNVG-18 Battery (Black)", OUT, "Prefabs/NVG/VNVS_GPNVG18_Battery_Black.et")]),
]


def strip(r):
    return re.sub(r"^\{[0-9A-F]{16}\}", "", r)


def res(r):
    p = strip(r)
    for root in (OUT, NVS):
        if os.path.exists(root + p):
            return root + p
    return None


def prefab_chain(root, rel):
    worn = over = None
    while rel:
        f = None
        for r in (root, NVS, OUT):
            if os.path.exists(r + rel):
                f = r + rel
                break
        if not f:
            break
        t = open(f, encoding="utf-8").read()
        if worn is None:
            m = re.search(r'WornModel "([^"]+)"', t)
            worn = strip(m.group(1)) if m else None
        if over is None:
            m = re.search(r'WornMaterialsOverride \{(.*?)\n   \}', t, re.S)
            if m:
                over = [strip(x) for x in re.findall(r'"(\{[0-9A-F]{16}\}[^"]+)"', m.group(1))]
        p = re.match(r'\w+ : "\{[0-9A-F]{16}\}([^"]+)"', t)
        rel = p.group(1) if p else None
    return worn, over


def emat_maps(emat):
    p = res(emat)
    if not p:
        return None
    e = open(p, encoding="utf-8").read()
    out = {"emat": os.path.basename(p)}
    for k in ("BCRMap", "NMOMap"):
        b = re.search(k + r' "([^"]+)"', e)
        if b:
            q = res(b.group(1))
            stem = (q or (NVS + strip(b.group(1))))[:-5]
            for ext in (".png", ".tif", ".tga"):
                if os.path.exists(stem + ext):
                    out[k] = stem + ext
                    break
    return out


g = {}
exec(open("C:/Users/lebea/Documents/Github/OUTLAWHELMETS/_tools/preview_sf_live.py").read().split("win = bpy.context")[0], g)
make_mat = g["material"]

scene = bpy.data.scenes[SCENE]
win = bpy.context.window_manager.windows[0]
win.scene = scene
report, missing = [], []
for colname, slot, items in ITEMS:
    col = bpy.data.collections.get(colname)
    if col is None or col.name not in scene.collection.children:
        col = bpy.data.collections.new(colname)
        scene.collection.children.link(col)
    first_new = len(col.objects) == 0
    for i, (label, root, rel) in enumerate(items):
        old = bpy.data.objects.get(label)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        worn, over = prefab_chain(root, rel)
        fbx = None
        for r in (OUT, NVS):
            if worn and os.path.exists(r + worn[:-4] + ".fbx"):
                fbx = r + worn[:-4] + ".fbx"
                meta = r + worn + ".meta"
                break
        if not fbx:
            missing.append(f"{label}: no fbx for {worn}")
            continue
        meta_t = open(meta, encoding="utf-8").read() if os.path.exists(meta) else ""
        assigns = re.findall(r'SourceMaterial "([^"]+)"\s*AssignedMaterial "([^"]+)"', meta_t)
        src_to_emat = {s: strip(e) for s, e in assigns}
        if over:
            for k, (s, _) in enumerate(assigns):
                if k < len(over):
                    src_to_emat[s] = over[k]
        before = set(bpy.data.objects)
        with bpy.context.temp_override(window=win, scene=scene):
            bpy.ops.import_scene.fbx(filepath=fbx)
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH" and not re.match(r"^(UTM|UCX|UBX|USP|UCS|UCL)", o.name)]
        M = (C @ Matrix(SLOT_MATS[slot]).transposed() @ C.inverted()) if slot else Matrix.Identity(4)
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = M @ mw
            for md in [m for m in o.modifiers if m.type == "ARMATURE"]:
                o.modifiers.remove(md)
            for s in o.material_slots:
                if s.material:
                    src = re.sub(r"\.\d{3}$", "", s.material.name)
                    mp = emat_maps(src_to_emat[src]) if src in src_to_emat else None
                    if not mp or not mp.get("BCRMap"):
                        missing.append(f"{label}: {src}")
                    s.material = make_mat(src, mp)
            for c in o.users_collection:
                c.objects.unlink(o)
            col.objects.link(o)
            o.name = label if len(meshes) == 1 else f"{label} - {o.name}"
            hide = (i > 0) or not first_new
            o.hide_set(hide)
            o.hide_render = hide
        for o in new:
            if o not in meshes:
                bpy.data.objects.remove(o, do_unlink=True)
        report.append((colname, label, os.path.basename(fbx), len(meshes), "hidden" if (i > 0 or not first_new) else "shown"))
for r in report:
    print(r)
print("MISSING", missing)
