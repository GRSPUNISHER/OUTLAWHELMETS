"""Maritime-only attachments and slots in SFHELMETS (python _tools/gen_maritime_acc.py, after build_maritime_acc.py).

User 2026-09-30: the AMP, PVS-31 BRS and ShawBrain pouch were re-fitted on the Maritime; they become separate "(Maritime)"
items (the SF / XP keep the originals). ShawBrain MC and RG share one geometry, so both colours get the Maritime fit
(per-colour xob, the colour's own emat). User "give it its own slots": the Maritime's Earpro / BRS / Battery slots use
Maritime-only area types, so only "(Maritime)" items fit them; the items of those slots that were not re-fitted (Comtac VII
RG/Tan, Comtac VI, BNVD battery) get "(Maritime)" prefab copies on the same models. FBXs already in place are not re-copied.
"""
import os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
exec(_src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")])

MFX = ROOT + "_tools/work/maritime/fbx/"
ACC = "ASSETS/Helmet Accessories/"
MT_AREAS = {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_MaritimeEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_MaritimeBRS",
            "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_MaritimeBattery"}
ITEMS = [
    ("MT_AMP", ACC + "AMP/Maritime/OpsCore_AMP_Maritime.fbx", ACC + "AMP/OpsCore_AMP.xob",
     "Prefabs/EarPro/OpsCore AMP (Maritime).et", "Ops-Core AMP (Maritime)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    ("MT_BRS", ACC + "BATTERYPACK/Maritime/batterypack_Maritime.fbx", ACC + "BATTERYPACK/batterypack.xob",
     "Prefabs/Batteries/PVS-31 BRS (MC) (Maritime).et", "PVS-31 BRS (MC) (Maritime)", "Helmet Attachment", "OUTLAW_Helmet_BRS"),
    ("MT_ShawBrain", ACC + "ShawBrainPouch/MC SHAWBRAIN/Maritime/shawbrainpouch_Maritime.fbx",
     ACC + "ShawBrainPouch/MC SHAWBRAIN/shawbrainpouch.xob", "Prefabs/Battery Pouches/ShawBrainPouch (MC) (Maritime).et",
     "ShawBrain Pouch (MC) (Maritime)", "Helmet Attachment", "OUTLAW_Helmet_Battery"),
    ("MT_ShawBrain", ACC + "ShawBrainPouch/RG SHAWBRAIN/Maritime/shawbrainpouch_Maritime.fbx",
     ACC + "ShawBrainPouch/RG SHAWBRAIN/shawbrainpouch.xob", "Prefabs/Battery Pouches/ShawBrainPouch (RG) (Maritime).et",
     "ShawBrain Pouch (RG) (Maritime)", "Helmet Attachment", "OUTLAW_Helmet_Battery"),
]

prefabs = []
for part, rel_fbx, orig_xob, prefab, name, desc, area in ITEMS:
    mats = existing_assigns(orig_xob)
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    for s, d in ((MFX + part + ".fbx", rel_fbx), (MFX + part + "_Item.fbx", item_fbx)):
        if not os.path.exists(ADDON + d):
            shutil.copyfile(s, ADDON + d)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    xob_meta(worn, mats, True)
    xob_meta(item, mats, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    accessory_prefab(prefab, name, desc, MT_AREAS[area], worn, item)
    prefabs.append(prefab)
    print(name, "->", MT_AREAS[area], mats)

COPIES = [("Prefabs/EarPro/Comtacs (RG).et", "Prefabs/EarPro/Comtacs (RG) (Maritime).et", "Comtac VII (RG) (Maritime)", "Ear Pro"),
          ("Prefabs/EarPro/Comtacs (Tan).et", "Prefabs/EarPro/Comtacs (Tan) (Maritime).et", "Comtac VII (Tan) (Maritime)", "Ear Pro"),
          ("Prefabs/EarPro/Comtac VI.et", "Prefabs/EarPro/Comtac VI (Maritime).et", "Comtac VI (Maritime)", "Ear Pro"),
          ("Prefabs/Batteries/BNVD Battery Pack.et", "Prefabs/Batteries/BNVD Battery Pack (Maritime).et", "BNVD Battery Pack (Maritime)",
           "Helmet Attachment")]
for src, prefab, name, desc in COPIES:
    s = read(src)
    area = re.search(r"AreaType (\w+) ", s).group(1)
    worn, item = (re.sub(r"^\{[0-9A-F]{16}\}", "", re.search(k + r' "([^"]+)"', s).group(1)) for k in ("WornModel", "ItemModel"))
    accessory_prefab(prefab, name, desc, MT_AREAS[area], worn, item)
    prefabs.append(prefab)
    print(name, "->", MT_AREAS[area], worn)

sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
for a in MT_AREAS.values():
    if f"class {a}:" not in sc:
        sc = sc.rstrip() + f"\n\nclass {a}: LoadoutAreaType{{}};\n"
write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc)

for code in ("AOR1", "MC", "MCB", "ODGreen", "RG", "Tan"):
    p = f"Prefabs/Helmets/Maritime/Maritime_Helmet_{code}.et"
    h = read(p)
    for old, new in MT_AREAS.items():
        h = h.replace(f"AreaType {old} ", f"AreaType {new} ")
    write(p, h)

CAT = "Configs/EntityCatalog/US/InventoryItems_EntityCatalog_US.conf"
cat = read(CAT)


def cat_entry(prefab, kind):
    k = "cat:" + prefab
    return (f'    SCR_EntityCatalogInventoryItem "{{{guid(k)}}}" {{\n     m_sEntityPrefab "{ref(prefab)}"\n'
            f'     m_aEntityDataList {{\n      SCR_ArsenalItem "{{{guid(k + ":ai")}}}" {{\n       m_eItemType {kind}\n'
            f'      }}\n     }}\n    }}\n')


i = cat.index('m_sIdentifier "Outlaw Helmet Accesories"')
j = cat.index("m_aEntities {\n", i) + len("m_aEntities {\n")
cat = cat[:j] + "".join(cat_entry(p, "EQUIPMENT") for p in prefabs if "{%s}" % rguid(p) not in cat) + cat[j:]
write(CAT, cat)
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
print("maritime attachments", len(prefabs))
