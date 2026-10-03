"""Interchangeable shells for every OUTLAW helmet (python _tools/gen_shells.py, after build_shells.py).

User 2026-09-30: "do the interchangeable shells for all the helmets" + "why do i have all the xp helmets prefabs still when i
only need one prefab" (answers: black (MCB) core, one helmet per family for SF V2, Maritime and XP).
Each family has ONE helmet prefab = the CORE (harness / chin strap / pads / shared liner, identical under every shell of the
family, in MCB) with a prefilled SHELL slot in a family-only area type (OUTLAW_Helmet_SFShell / MaritimeShell / XPShell); every
helmet type and colour is a shell item (SF Bump / Ballistic, Maritime, XP / XP 4-Hole / XP Carbon / XP Carbon 4-Hole, x6
colours). Rails and every attachment slot stay on the core. The old per-colour / per-type helmet prefabs, their catalog
entries and the unused non-MCB cores are removed.

Armor (ARMOR_ON = "shell"): the UTM_Helmet hit zone, its gamemat (Bump armor_5mm, others hard_aramid) and
SCR_ArmorDamageManagerComponent live on the shell - vanilla SCR_ArmorDamageManagerComponent.HijackDamageHandling walks
GetParent() up to the character, so a shell in the core's slot still passes damage to the wearer (the helmet knock-off
only looks at the direct parent, so it no longer fires). Shells are GameEntity (ColliderHistoryComponent needs it).

Helmet prefabs are owned by this script (gen_sf / gen_maritime / gen_xp / split_rear_slots write the old one-piece helmets).
Material assigns are read from the old one-piece helmet xob metas, so those models stay on disk.
"""
import difflib, glob, os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
exec(_src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")])

ARMOR_ON = "shell"
CORE_CODE = "MCB"
SFX = ROOT + "_tools/work/shells/fbx/"
REPORT = json.load(open(ROOT + "_tools/work/shells/report.json"))
SF_BASE = "Prefabs/Helmets/SF V2 Helmets/SF_Helmet_AOR1 (base dont touch).et"
SLOTS_TEXT = "Interchangeable shell, removable rails, ear pro, BRS, battery, counterweight, scrim, NVG, light and strobe slots."
CODES = [("AOR1", "AOR1"), ("MC", "MC"), ("MCB", "MCB"), ("ODGreen", "OD Green"), ("RG", "RG"), ("Tan", "Tan")]
SF_FOLDER = {"AOR1": "HELMET AOR1", "MC": "HELMET MC", "MCB": "HELMET BLACK", "ODGreen": "HELMET GREEN", "RG": "HELMET RG",
             "Tan": "HELMET TAN"}
MT_AREAS = {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_MaritimeEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_MaritimeBRS",
            "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_MaritimeBattery"}
XP_AREAS = {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_XPEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_XPBRS", "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_XPBattery",
            "OUTLAW_Helmet_Counterweight": "OUTLAW_Helmet_XPCounterweight", "OUTLAW_Helmet_Scrim": "OUTLAW_Helmet_XPScrim"}


def sf_dir(c): return f"ASSETS/{SF_FOLDER[c]}/"
def mt_dir(c): return f"ASSETS/MARITIME/MARITIME {c}/"
def xp_dir(c): return f"ASSETS/XP/XP {c}/"


# type -> (shell file stem, material source xob stem, UTM gamemat, shell prefab stem, shell name)
FAMILIES = {
    "SF": dict(core="SF_Core", dir=sf_dir, core_file="SF V2 Core", core_src="SF V2 Bump", area="OUTLAW_Helmet_SFShell",
               rails_area="OUTLAW_Helmet_Rails", areas={}, pf="Prefabs/Helmets/SF V2 Helmets/Shells/",
               helmet=SF_BASE, name="SF V2 Helmet", default="SF_Ballistic",
               rails="Prefabs/Helmets/SF V2 Helmets/Rails/SF_Rails_MCB.et",
               old=["Prefabs/Helmets/SF V2 Helmets/SF_Helmet_*.et", "Prefabs/Helmets/SF V2 Helmets/SF_Ballistic_Helmet_*.et"],
               types={"SF_Bump": ("SF V2 Bump Shell", "SF V2 Bump", GM_BUMP, "SF_BumpShell", "SF V2 Bump Shell"),
                      "SF_Ballistic": ("SF V2 Ballistic Shell", "SF V2 Ballistic", GM_BALLISTIC, "SF_BallisticShell", "SF V2 Ballistic Shell")}),
    "MT": dict(core="MT_Core", dir=mt_dir, core_file="MaritimeCore", core_src="Maritime", area="OUTLAW_Helmet_MaritimeShell",
               rails_area="OUTLAW_Helmet_MaritimeRails", areas=MT_AREAS, pf="Prefabs/Helmets/Maritime/Shells/",
               helmet="Prefabs/Helmets/Maritime/Maritime_Helmet.et", name="Ops-Core Maritime Helmet", default="MT",
               rails="Prefabs/Helmets/Maritime/Rails/Maritime_Rails_MCB.et", old=["Prefabs/Helmets/Maritime/Maritime_Helmet_*.et"],
               types={"MT": ("MaritimeShell", "Maritime", GM_BALLISTIC, "Maritime_Shell", "Ops-Core Maritime Shell")}),
    "XP": dict(core="XP_Core", dir=xp_dir, core_file="XPCore", core_src="XP3", area="OUTLAW_Helmet_XPShell",
               rails_area="OUTLAW_Helmet_XPRails", areas=XP_AREAS, pf="Prefabs/Helmets/XP/Shells/",
               helmet="Prefabs/Helmets/XP/XP_Helmet.et", name="Ops-Core FAST XP Helmet", default="XP3",
               rails="Prefabs/Helmets/XP/Rails/XP_Rails_MCB.et", old=["Prefabs/Helmets/XP/XP*_Helmet_*.et"],
               types={k: (k + "Shell", k, GM_BALLISTIC, k + "_Shell", n + " Shell")
                      for k, n in (("XP3", "Ops-Core FAST XP"), ("XP4", "Ops-Core FAST XP 4-Hole"), ("XPC3", "Ops-Core FAST XP Carbon"),
                                   ("XPC4", "Ops-Core FAST XP Carbon 4-Hole"))}),
}

ARMOR = '''  ColliderHistoryComponent "{C_HIST}" {
  }
  SCR_ArmorDamageManagerComponent "{C_ARMOR}" {
   "Additional hit zones" {
    SCR_ArmorHitZone helmet {
     ColliderNames {
      "UTM_Helmet"
     }
     HZDefault 1
     MaxHealth 10000
     m_eHitZoneGroup HEAD
    }
   }
   m_fPassedDamageScale 4
   m_bIsDetachable 0
  }
'''


def place(part, rel_fbx, mats, utm_gm):
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    for s, d in ((SFX + part + ".fbx", rel_fbx), (SFX + part + "_Item.fbx", item_fbx)):
        if not os.path.exists(ADDON + d):
            shutil.copyfile(s, ADDON + d)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    if not os.path.exists(ADDON + worn + ".meta"):
        xob_meta(worn, mats, True, [("UTM_Helmet", "FireGeo", utm_gm)] if utm_gm else [])
    if not os.path.exists(ADDON + item + ".meta"):
        xob_meta(item, mats, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    return worn, item


def mats_for(src_xob, names):
    a = dict(existing_assigns(src_xob))
    missing = [n for n in names if n not in a]
    if missing:
        raise SystemExit(f"{src_xob}: no material assign for {missing}")
    return [(n, a[n]) for n in names]


def shell_prefab(rel, name, desc, area, worn, item):
    accessory_prefab(rel, name, desc, area, worn, item)
    t = read(rel)
    k = "c:" + rel + ":"
    t = t.replace("GenericEntity {\n", "GameEntity {\n", 1)
    if ARMOR_ON == "shell":
        t = t.replace("  MeshObject ", ARMOR.replace("C_HIST", guid(k + "ColliderHistoryComponent"))
                      .replace("C_ARMOR", guid(k + "SCR_ArmorDamageManagerComponent")) + "  MeshObject ", 1)
        t = t.replace("   ItemModel " + f'"{ref(item)}"\n', "   ItemModel " + f'"{ref(item)}"\n   PhysicsOnWearEnabled 1\n   AnimateCollidersOnWear 1\n', 1)
    t = t.replace("     SizeSetupStrategy Manual\n     ItemVolume 10\n",
                  "     Weight 1\n     SizeSetupStrategy Manual\n     ItemDimensions 20 20 15\n     ItemVolume 2000\n", 1)
    t = t.replace("   Mass 0.3\n", "   Mass 1\n", 1)
    t = t.replace("      CameraOrbitAngles -25 30 0\n      CameraDistanceToItem 1\n",
                  "      CameraOrbitAngles -25 25 0\n      CameraDistanceToItem 1.5\n      CameraOffset 0 -0.02 0\n", 1)
    write(rel, t)


def remove_resource(rel_noext_list):
    for base_ in rel_noext_list:
        for f in glob.glob(glob.escape(ADDON + base_) + "*"):
            os.remove(f)


# ================================================================ models + shell prefabs
shells, cores = {}, {}
for fam, F in FAMILIES.items():
    for code, pretty in CODES:
        d = F["dir"](code)
        core_stem = d + F["core_file"]
        if code == CORE_CODE:
            cores[fam] = place(F["core"], core_stem + ".fbx", mats_for(d + F["core_src"] + ".xob", REPORT[F["core"]]["mats"]), None)
        else:
            remove_resource([core_stem + ".", core_stem + "_Item."])
        for t, (stem, src, gm, pstem, sname) in F["types"].items():
            worn, item = place(t + "_ShellOnly", d + stem + ".fbx", mats_for(d + src + ".xob", REPORT[t]["shell_mats"]), gm)
            p = f"{F['pf']}{pstem}_{code}.et"
            shell_prefab(p, f"{sname} ({pretty})", f"Interchangeable {sname.lower().replace(' shell', '')} shell. Carries the helmet's ballistic protection.",
                         F["area"], worn, item)
            shells[(t, code)] = p
    print(fam, "MCB core + shells placed")

sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
for F in FAMILIES.values():
    if f"class {F['area']}:" not in sc:
        sc = sc.rstrip() + f"\n\nclass {F['area']}: LoadoutAreaType{{}};\n"
write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc)


def set_names(x, name, model):
    x = re.sub(r'(ClothNodeStorageComponent[\s\S]*?Name )"[^"]*"(\s*Description )"[^"]*"',
               lambda m: m.group(1) + f'"{name}"' + m.group(2) + f'"Modular {model} helmet. {SLOTS_TEXT}"', x, count=1)
    return re.sub(r'(InventoryItemComponent[\s\S]*?Name )"[^"]*"', lambda m: m.group(1) + f'"{name}"', x, count=1)


# ================================================================ SF V2 helmet = the base prefab (core + shell slot)
ARMOR_RE = r'  SCR_ArmorDamageManagerComponent "\{[0-9A-F]{16}\}" \{\n(?:   .*\n)*?  \}\n'
F = FAMILIES["SF"]
base = read(SF_BASE)
cw, ci = cores["SF"]
if ARMOR_ON == "shell":
    base = re.sub(ARMOR_RE, "", base, count=1)
base = re.sub(r'(MeshObject "\{[0-9A-F]{16}\}" \{\s*Object )"[^"]*"', lambda m: m.group(1) + f'"{ref(ci)}"', base, count=1)
base = re.sub(r'WornModel "[^"]*"', f'WornModel "{ref(cw)}"', base)
base = re.sub(r'ItemModel "[^"]*"', f'ItemModel "{ref(ci)}"', base)
base = base.replace("     Weight 1.5\n", "     Weight 0.5\n", 1).replace("   Mass 1.5\n", "   Mass 0.5\n", 1)
if "LoadoutSlotInfo Shell" not in base:
    base = base.replace("   Slots {\n", f'   Slots {{\n    LoadoutSlotInfo Shell {{\n     Prefab ""\n     InheritParentSkeleton 1\n'
                        f'     AreaType OUTLAW_Helmet_SFShell "{{{guid("c:base:area_shell")}}}" {{\n     }}\n    }}\n', 1)
base = re.sub(r'(LoadoutSlotInfo Shell \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{ref(shells[(F["default"], CORE_CODE)])}"', base)
base = re.sub(r'(LoadoutSlotInfo Rails \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{ref(F["rails"])}"', base)
base = set_names(base, F["name"], "SF V2")
write(SF_BASE, base)


# ================================================================ Maritime / XP helmet = derived from the SF base
def derive(p, fam):
    F = FAMILIES[fam]
    worn, item = cores[fam]
    x = base
    x = re.sub(r'(?m)^ ID "[0-9A-F]{16}"', f' ID "{guid("id:" + p)}"', x, count=1)
    x = re.sub(r'"\{([0-9A-F]{16})\}"', lambda m: '"{%s}"' % guid(f"c:{p}:{m.group(1)}"), x)
    x = re.sub(r'(LoadoutSlotInfo Rails \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{ref(F["rails"])}"', x)
    x = re.sub(r'(LoadoutSlotInfo Shell \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{ref(shells[(F["default"], CORE_CODE)])}"', x)
    x = x.replace("AreaType OUTLAW_Helmet_Rails ", f"AreaType {F['rails_area']} ").replace("AreaType OUTLAW_Helmet_SFShell ", f"AreaType {F['area']} ")
    for o, n in F["areas"].items():
        x = x.replace(f"AreaType {o} ", f"AreaType {n} ")
    return set_names(x, F["name"], F["name"].replace(" Helmet", ""))


for fam in ("MT", "XP"):
    p = FAMILIES[fam]["helmet"]
    write(p, derive(p, fam))
    if not os.path.exists(ADDON + p + ".meta"):
        simple_meta(p, "EntityTemplateResourceClass")

# ================================================================ remove the old per-colour / per-type helmets
removed = {}
for F in FAMILIES.values():
    for pat in F["old"]:
        for full in glob.glob(ADDON + pat):
            rel = full[len(ADDON):].replace("\\", "/")
            if rel == SF_BASE:
                continue
            removed[rel] = meta_guid(rel)
            os.remove(full)
            if os.path.exists(full + ".meta"):
                os.remove(full + ".meta")

# ================================================================ catalog
CAT = "Configs/EntityCatalog/US/InventoryItems_EntityCatalog_US.conf"
cat = read(CAT)
dropped = 0
for rel, g in removed.items():
    if g:
        cat, n = re.subn(r'    SCR_EntityCatalogInventoryItem "\{[0-9A-F]{16}\}" \{\n     m_sEntityPrefab "\{%s\}[^"]*"\n(?:     .*\n)*?    \}\n' % g, "", cat)
        dropped += n


def cat_entry(prefab, kind):
    k = "cat:" + prefab
    return (f'    SCR_EntityCatalogInventoryItem "{{{guid(k)}}}" {{\n     m_sEntityPrefab "{ref(prefab)}"\n'
            f'     m_aEntityDataList {{\n      SCR_ArsenalItem "{{{guid(k + ":ai")}}}" {{\n       m_eItemType {kind}\n'
            f'      }}\n     }}\n    }}\n')


def add_to_list(text, ident, prefabs, kind):
    i = text.index(f'm_sIdentifier "{ident}"')
    j = text.index("m_aEntities {\n", i) + len("m_aEntities {\n")
    return text[:j] + "".join(cat_entry(p, kind) for p in prefabs if "{%s}" % rguid(p) not in text) + text[j:]


cat = add_to_list(cat, "Outlaw Helmets", [F["helmet"] for F in FAMILIES.values()], "HEADWEAR")
cat = add_to_list(cat, "Outlaw Helmet Accesories", list(shells.values()), "EQUIPMENT")
write(CAT, cat)
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
print("shell prefabs", len(shells), "helmets", [F["helmet"] for F in FAMILIES.values()],
      "old helmet prefabs removed", len(removed), "catalog entries dropped", dropped)
