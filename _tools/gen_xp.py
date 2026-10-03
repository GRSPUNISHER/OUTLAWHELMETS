"""Place the Ops-Core FAST XP / XP Carbon (3-hole, 4-hole) into SFHELMETS (python _tools/gen_xp.py).

SUPERSEDED 2026-09-30 for helmet PREFABS: helmets are now one core + interchangeable shell per family, written by
gen_shells.py. Rerunning this script's helmet section brings back the old per-colour one-piece helmets.


After build_xp.py and export_helmet_colours.py xp + xp4 (texture sets XP1 / Carbon1 / XP4M, the user's MCB HELMET.spp stack, 2048;
XP1H4 = XP1 baked on the 4-hole shells, used by XP4 / XPC4 so they carry no 3-hole shroud-frame AO).
Helmet = shell (hit zone) + removable XP rails (own slot type) + the SF attachment slots that PASSED the every-vertex clip check
(clip_check_xp.py) at first; user 2026-09-30: every SF slot goes on every helmet, so Earpro and Scrims are kept; the slots whose
items the user re-fitted for the XP use XP-only area types (XP_AREAS, items from gen_xp_acc.py). Texture metas carry MaxSize "2048". Helmet prefab = the SF base prefab structure with its own ids.
"""
import os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
exec(_src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")])

XFX = ROOT + "_tools/work/xp/fbx/"
EXP = ROOT + "_tools/work/painter/export/"
XA = "ASSETS/XP/"
PF = "Prefabs/Helmets/XP/"
RAIL_AREA = "OUTLAW_Helmet_XPRails"
XP_AREAS = {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_XPEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_XPBRS",
            "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_XPBattery", "OUTLAW_Helmet_Counterweight": "OUTLAW_Helmet_XPCounterweight",
            "OUTLAW_Helmet_Scrim": "OUTLAW_Helmet_XPScrim"}
DROP_SLOTS = ()
SF_BASE = "Prefabs/Helmets/SF V2 Helmets/SF_Helmet_AOR1 (base dont touch).et"
COLOURS = [("AOR1", "AOR1", "AOR1"), ("MC", "MC", "MC"), ("MCB", "MCB", "MCB"), ("ODGreen", "OD", "OD Green"),
           ("RG", "RG", "RG"), ("Tan", "TAN", "Tan")]
MODELS = [("XP3", "Ops-Core FAST XP", ("XP1",)), ("XP4", "Ops-Core FAST XP 4-Hole", ("XP1", "XP4M")),
          ("XPC3", "Ops-Core FAST XP Carbon", ("Carbon1", "XP1")), ("XPC4", "Ops-Core FAST XP Carbon 4-Hole", ("Carbon1", "XP1", "XP4M"))]


def place_x(part, rel_fbx, materials, utm_gm=None):
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    shutil.copyfile(XFX + part + ".fbx", ADDON + rel_fbx)
    shutil.copyfile(XFX + part + "_Item.fbx", ADDON + item_fbx)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    xob_meta(worn, materials, True, [("UTM_Helmet", "FireGeo", utm_gm)] if utm_gm else [])
    xob_meta(item, materials, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    return worn, item


def drop_slot(text, name):
    return re.sub(r"    LoadoutSlotInfo " + name + r" \{\n(?:     .*\n)*?    \}\n", "", text, count=1)


sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
if RAIL_AREA not in sc:
    write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc.rstrip() + f"\n\nclass {RAIL_AREA}: LoadoutAreaType{{}};\n")

sf_base = read(SF_BASE)
helmets, rails = [], []
for code, tag, pretty in COLOURS:
    folder = f"{XA}XP {code}/"
    d = folder + "Data/"
    os.makedirs(ADDON + d, exist_ok=True)
    emats = {}
    for tset in ("XP1", "Carbon1", "XP4M", "XP1H4"):
        stem = f"{code}XP_{tset}"
        for kind in ("BCR", "NMO"):
            shutil.copyfile(f"{EXP}{tset}_{tag}_{kind}.png", f"{ADDON}{d}{stem}_{kind}.png")
        edds_meta(d + stem + "_BCR.edds"); edds_meta(d + stem + "_NMO.edds")
        emat(d + f"XP_{tset}.emat", d + stem + "_BCR.edds", d + stem + "_NMO.edds")
        emats[tset] = ref(d + f"XP_{tset}.emat")
    rw, ri = place_x("XP_Rails", folder + "XPRails.fbx", [("XP1", emats["XP1"])])
    rp = f"{PF}Rails/XP_Rails_{code}.et"
    accessory_prefab(rp, f"FAST XP Rails ({pretty})", "Removable rails for the Ops-Core FAST XP / XP Carbon helmets.", RAIL_AREA, rw, ri)
    rails.append(rp)
    for key, model, sets in MODELS:
        worn, item = place_x(key + "_Shell", folder + f"{key}.fbx",
                             [(s, emats["XP1H4" if (s == "XP1" and key in ("XP4", "XPC4")) else s]) for s in sets], GM_BALLISTIC)
        p = f"{PF}{key}_Helmet_{code}.et"
        t = sf_base
        t = re.sub(r'(?m)^ ID "[0-9A-F]{16}"', f' ID "{guid("id:" + p)}"', t, count=1)
        t = re.sub(r'"\{([0-9A-F]{16})\}"', lambda m: '"{%s}"' % guid(f"c:{p}:{m.group(1)}"), t)
        t = re.sub(r'(MeshObject "\{[0-9A-F]{16}\}" \{\s*Object )"[^"]*"', lambda m: m.group(1) + f'"{ref(item)}"', t, count=1)
        t = re.sub(r'WornModel "[^"]*"', f'WornModel "{ref(worn)}"', t)
        t = re.sub(r'ItemModel "[^"]*"', f'ItemModel "{ref(item)}"', t)
        t = re.sub(r'(LoadoutSlotInfo Rails \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{ref(rp)}"', t)
        t = t.replace("AreaType OUTLAW_Helmet_Rails ", f"AreaType {RAIL_AREA} ")
        for _o, _n in XP_AREAS.items():
            t = t.replace(f"AreaType {_o} ", f"AreaType {_n} ")
        for s in DROP_SLOTS:
            t = drop_slot(t, s)
        t = re.sub(r'(ClothNodeStorageComponent[\s\S]*?Name )"[^"]*"(\s*Description )"[^"]*"',
                   lambda m: m.group(1) + f'"{model} ({pretty})"' + m.group(2) +
                   '"Modular ' + model + ' helmet. Removable rails, ear pro, BRS, battery, counterweight, scrim, NVG, light and strobe slots."', t, count=1)
        t = re.sub(r'(InventoryItemComponent[\s\S]*?Name )"[^"]*"', lambda m: m.group(1) + f'"{model} ({pretty})"', t, count=1)
        write(p, t)
        if not os.path.exists(ADDON + p + ".meta"):
            simple_meta(p, "EntityTemplateResourceClass")
        helmets.append(p)

CAT = "Configs/EntityCatalog/US/InventoryItems_EntityCatalog_US.conf"
cat = read(CAT)


def cat_entry(prefab, kind):
    k = "cat:" + prefab
    return (f'    SCR_EntityCatalogInventoryItem "{{{guid(k)}}}" {{\n     m_sEntityPrefab "{ref(prefab)}"\n'
            f'     m_aEntityDataList {{\n      SCR_ArsenalItem "{{{guid(k + ":ai")}}}" {{\n       m_eItemType {kind}\n'
            f'      }}\n     }}\n    }}\n')


def add_to_list(text, ident, prefabs, kind):
    i = text.index(f'm_sIdentifier "{ident}"')
    j = text.index("m_aEntities {\n", i) + len("m_aEntities {\n")
    return text[:j] + "".join(cat_entry(p, kind) for p in prefabs if "{%s}" % rguid(p) not in text) + text[j:]


cat = add_to_list(cat, "Outlaw Helmets", helmets, "HEADWEAR")
cat = add_to_list(cat, "Outlaw Helmet Accesories", rails, "EQUIPMENT")
write(CAT, cat)
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
print("xp helmets", len(helmets), "rails", len(rails))
