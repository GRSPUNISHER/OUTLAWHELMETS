"""XP-only attachments and slots in SFHELMETS (python _tools/gen_xp_acc.py, after build_xp_acc.py).

User 2026-09-30 re-fitted every attachment except the BNVD battery on the FAST XP / XP Carbon helmets (one fit for all
four); they become separate "(XP)" items (the SF / Maritime keep theirs). Colour variants share one geometry (Comtac VII
RG/Tan, ShawBrain MC/RG, both scrims MC/RG): per-colour xob with the colour's own emat. Same as the Maritime ("give it its
own slots"): every XP slot that holds a re-fitted item uses an XP-only area type - Earpro, BRS, Battery, Counterweight,
Scrims - so only "(XP)" items fit them; the BNVD battery, which was not re-fitted, gets an "(XP)" prefab copy on the same
model. Rails were XP-only already; NVG / Light / Strobe stay shared. FBXs already in place are not re-copied.
"""
import os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
exec(_src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")])

XFX = ROOT + "_tools/work/xp/fbx/"
ACC = "ASSETS/Helmet Accessories/"
XP_AREAS = {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_XPEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_XPBRS",
            "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_XPBattery", "OUTLAW_Helmet_Counterweight": "OUTLAW_Helmet_XPCounterweight",
            "OUTLAW_Helmet_Scrim": "OUTLAW_Helmet_XPScrim"}
# part, new worn fbx, xob whose material assigns are reused, prefab, name, description, area of the original item
ITEMS = [
    ("XP_AMP", ACC + "AMP/XP/OpsCore_AMP_XP.fbx", ACC + "AMP/OpsCore_AMP.xob",
     "Prefabs/EarPro/OpsCore AMP (XP).et", "Ops-Core AMP (XP)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    ("XP_Comtac7", ACC + "COMTACS/RG COMTACS/XP/comtacviinostrap_XP.fbx", ACC + "COMTACS/RG COMTACS/comtacviinostrap.xob",
     "Prefabs/EarPro/Comtacs (RG) (XP).et", "Comtac VII (RG) (XP)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    ("XP_Comtac7", ACC + "COMTACS/TAN COMTACS/XP/comtacviinostrap_XP.fbx", ACC + "COMTACS/TAN COMTACS/comtacviinostrap.xob",
     "Prefabs/EarPro/Comtacs (Tan) (XP).et", "Comtac VII (Tan) (XP)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    ("XP_Comtac6", ACC + "COMTACS/COMTAC VI/XP/comtacvi_XP.fbx", ACC + "COMTACS/COMTAC VI/comtacvi.xob",
     "Prefabs/EarPro/Comtac VI (XP).et", "Comtac VI (XP)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    ("XP_BRS", ACC + "BATTERYPACK/XP/batterypack_XP.fbx", ACC + "BATTERYPACK/batterypack.xob",
     "Prefabs/Batteries/PVS-31 BRS (MC) (XP).et", "PVS-31 BRS (MC) (XP)", "Helmet Attachment", "OUTLAW_Helmet_BRS"),
    ("XP_ShawBrain", ACC + "ShawBrainPouch/MC SHAWBRAIN/XP/shawbrainpouch_XP.fbx",
     ACC + "ShawBrainPouch/MC SHAWBRAIN/shawbrainpouch.xob", "Prefabs/Battery Pouches/ShawBrainPouch (MC) (XP).et",
     "ShawBrain Pouch (MC) (XP)", "Helmet Attachment", "OUTLAW_Helmet_Battery"),
    ("XP_ShawBrain", ACC + "ShawBrainPouch/RG SHAWBRAIN/XP/shawbrainpouch_XP.fbx",
     ACC + "ShawBrainPouch/RG SHAWBRAIN/shawbrainpouch.xob", "Prefabs/Battery Pouches/ShawBrainPouch (RG) (XP).et",
     "ShawBrain Pouch (RG) (XP)", "Helmet Attachment", "OUTLAW_Helmet_Battery"),
    ("XP_Counterweight", ACC + "COUNTERWEIGHT/XP/counterweight_XP.fbx", ACC + "COUNTERWEIGHT/counterweight.xob",
     "Prefabs/Batteries/OpsCore Counterweight (Coyote) (XP).et", "Ops-Core Counterweight (Coyote) (XP)", "Helmet Attachment",
     "OUTLAW_Helmet_Counterweight"),
    ("XP_ScrimOak", ACC + "Scrims/HighCut Oak MC/XP/HighCut Scrim Oak_XP.fbx", ACC + "Scrims/HighCut Oak MC/HighCut Scrim Oak.xob",
     "Prefabs/Scrims/HighCut Oak Scrim (MC) (XP).et", "HighCut Oak Scrim (MC) (XP)", "Helmet Attachment", "OUTLAW_Helmet_Scrim"),
    ("XP_ScrimOak", ACC + "Scrims/HighCut Ranger Green/XP/HighCut Scrim Oak_XP.fbx",
     ACC + "Scrims/HighCut Ranger Green/HighCut Scrim Oak.xob", "Prefabs/Scrims/HighCut Oak Scrim (RG) (XP).et",
     "HighCut Oak Scrim (RG) (XP)", "Helmet Attachment", "OUTLAW_Helmet_Scrim"),
    ("XP_ScrimSemi", ACC + "Scrims/HighCut Semi MC/XP/HighCut Scrim Semi_XP.fbx", ACC + "Scrims/HighCut Semi MC/HighCut Scrim Oak.xob",
     "Prefabs/Scrims/HighCut SemiCircle Scrim (MC) (XP).et", "HighCut SemiCircle Scrim (MC) (XP)", "Helmet Attachment",
     "OUTLAW_Helmet_Scrim"),
    ("XP_ScrimSemi", ACC + "Scrims/HighCut Semi RG/XP/HighCut Scrim Semi_XP.fbx", ACC + "Scrims/HighCut Semi RG/HighCut Scrim Oak.xob",
     "Prefabs/Scrims/HighCut SemiCircle Scrim (RG) (XP).et", "HighCut SemiCircle Scrim (RG) (XP)", "Helmet Attachment",
     "OUTLAW_Helmet_Scrim"),
]

prefabs = []
for part, rel_fbx, orig_xob, prefab, name, desc, area in ITEMS:
    mats = existing_assigns(orig_xob)
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    for s, d in ((XFX + part + ".fbx", rel_fbx), (XFX + part + "_Item.fbx", item_fbx)):
        if not os.path.exists(ADDON + d):
            shutil.copyfile(s, ADDON + d)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    xob_meta(worn, mats, True)
    xob_meta(item, mats, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    accessory_prefab(prefab, name, desc, XP_AREAS[area], worn, item)
    prefabs.append(prefab)
    print(name, "->", XP_AREAS[area], mats)

COPIES = [("Prefabs/Batteries/BNVD Battery Pack.et", "Prefabs/Batteries/BNVD Battery Pack (XP).et", "BNVD Battery Pack (XP)",
           "Helmet Attachment")]
for src, prefab, name, desc in COPIES:
    s = read(src)
    area = re.search(r"AreaType (\w+) ", s).group(1)
    worn, item = (re.sub(r"^\{[0-9A-F]{16}\}", "", re.search(k + r' "([^"]+)"', s).group(1)) for k in ("WornModel", "ItemModel"))
    accessory_prefab(prefab, name, desc, XP_AREAS[area], worn, item)
    prefabs.append(prefab)
    print(name, "->", XP_AREAS[area], worn)

sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
for a in XP_AREAS.values():
    if f"class {a}:" not in sc:
        sc = sc.rstrip() + f"\n\nclass {a}: LoadoutAreaType{{}};\n"
write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc)

n_helmets = 0
for key in ("XP3", "XP4", "XPC3", "XPC4"):
    for code in ("AOR1", "MC", "MCB", "ODGreen", "RG", "Tan"):
        p = f"Prefabs/Helmets/XP/{key}_Helmet_{code}.et"
        h = read(p)
        for old, new in XP_AREAS.items():
            h = h.replace(f"AreaType {old} ", f"AreaType {new} ")
        write(p, h)
        n_helmets += 1

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
print("xp attachments", len(prefabs), "helmets", n_helmets)
