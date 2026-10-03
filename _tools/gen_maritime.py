"""Place the Ops-Core Maritime into SFHELMETS and write its Workbench resources (python _tools/gen_maritime.py).

SUPERSEDED 2026-09-30 for helmet PREFABS: helmets are now one core + interchangeable shell per family, written by
gen_shells.py. Rerunning this script's helmet section brings back the old per-colour one-piece helmets.


After build_maritime.py (FBX: SF placement + the SF's chin strap) and the Painter export (the user's MCB HELMET.spp stack, per
colourway, texture sets MT + KitA, 2048). Helmet = shell (hit zone) + removable Maritime rails in their own slot type + the SF
attachment slots (same slot types/offsets as the SF: same FAST family, same placement). Every texture meta has MaxSize "2048".
The helmet prefab is the SF base prefab's structure (slots/values) with its own ids.
"""
import os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
exec(_src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")])

MFX = ROOT + "_tools/work/maritime/fbx/"
EXP = ROOT + "_tools/work/painter/export/"
MA = "ASSETS/MARITIME/"
PF = "Prefabs/Helmets/Maritime/"
RAIL_AREA = "OUTLAW_Helmet_MaritimeRails"
SF_BASE = "Prefabs/Helmets/SF V2 Helmets/SF_Helmet_AOR1 (base dont touch).et"
COLOURS = [("AOR1", "AOR1", "AOR1"), ("MC", "MC", "MC"), ("MCB", "MCB", "MCB"), ("ODGreen", "OD", "OD Green"),
           ("RG", "RG", "RG"), ("Tan", "TAN", "Tan")]


def place_mt(part, rel_fbx, materials, utm_gm=None):
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    shutil.copyfile(MFX + part + ".fbx", ADDON + rel_fbx)
    shutil.copyfile(MFX + part + "_Item.fbx", ADDON + item_fbx)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    xob_meta(worn, materials, True, [("UTM_Helmet", "FireGeo", utm_gm)] if utm_gm else [])
    xob_meta(item, materials, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    return worn, item


sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
if RAIL_AREA not in sc:
    write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc.rstrip() + f"\n\nclass {RAIL_AREA}: LoadoutAreaType{{}};\n")

sf_base = read(SF_BASE)
helmets, rails = [], []
for code, tag, pretty in COLOURS:
    folder = f"{MA}MARITIME {code}/"
    d = folder + "Data/"
    os.makedirs(ADDON + d, exist_ok=True)
    mats = []
    for tset in ("MT", "KitA"):
        stem = f"{code}Maritime{tset}"
        for kind in ("BCR", "NMO"):
            shutil.copyfile(f"{EXP}{tset}_{tag}_{kind}.png", f"{ADDON}{d}{stem}_{kind}.png")
        edds_meta(d + stem + "_BCR.edds"); edds_meta(d + stem + "_NMO.edds")
        emat(d + f"Maritime{tset}.emat", d + stem + "_BCR.edds", d + stem + "_NMO.edds")
        mats.append((tset, ref(d + f"Maritime{tset}.emat")))
    worn, item = place_mt("MT_Shell", folder + "Maritime.fbx", mats, GM_BALLISTIC)
    rw, ri = place_mt("MT_Rails", folder + "MaritimeRails.fbx", mats)
    rp = f"{PF}Rails/Maritime_Rails_{code}.et"
    accessory_prefab(rp, f"Maritime Rails ({pretty})", "Removable rails for the Ops-Core Maritime helmet.", RAIL_AREA, rw, ri)
    rails.append(rp)

    # helmet prefab: the SF base prefab (the user's slot set/values) with fresh ids, Maritime meshes and the Maritime rails slot
    p = f"{PF}Maritime_Helmet_{code}.et"
    t = sf_base
    t = re.sub(r'(?m)^ ID "[0-9A-F]{16}"', f' ID "{guid("id:" + p)}"', t, count=1)
    t = re.sub(r'"\{([0-9A-F]{16})\}"', lambda m: '"{%s}"' % guid(f"c:{p}:{m.group(1)}"), t)
    t = re.sub(r'(MeshObject "\{[0-9A-F]{16}\}" \{\s*Object )"[^"]*"', lambda m: m.group(1) + f'"{ref(item)}"', t, count=1)
    t = re.sub(r'WornModel "[^"]*"', f'WornModel "{ref(worn)}"', t)
    t = re.sub(r'ItemModel "[^"]*"', f'ItemModel "{ref(item)}"', t)
    t = re.sub(r'(LoadoutSlotInfo Rails \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{ref(rp)}"', t)
    t = t.replace("AreaType OUTLAW_Helmet_Rails ", f"AreaType {RAIL_AREA} ")
    for _o, _n in {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_MaritimeEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_MaritimeBRS", "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_MaritimeBattery"}.items():
        t = t.replace(f"AreaType {_o} ", f"AreaType {_n} ")
    t = re.sub(r'(ClothNodeStorageComponent[\s\S]*?Name )"[^"]*"(\s*Description )"[^"]*"',
               lambda m: m.group(1) + f'"Ops-Core Maritime ({pretty})"' + m.group(2) +
               '"Modular Ops-Core Maritime helmet. Removable rails, ear pro, BRS, battery, counterweight, scrim, NVG, light and strobe slots."', t, count=1)
    t = re.sub(r'(InventoryItemComponent[\s\S]*?Name )"[^"]*"', lambda m: m.group(1) + f'"Ops-Core Maritime ({pretty})"', t, count=1)
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
print("maritime helmets", len(helmets), "rails", len(rails))
