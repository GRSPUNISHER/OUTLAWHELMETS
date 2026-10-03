"""Give the BRS, the battery and the counterweight their own helmet slots, and put every SF slot on every helmet

SUPERSEDED 2026-09-30 for helmet PREFABS: helmets are now one core + interchangeable shell per family, written by
gen_shells.py. Rerunning this script's helmet section brings back the old per-colour one-piece helmets.

(python _tools/split_rear_slots.py).

User 2026-09-30: everything that goes on the SF goes on the other helmets; BRS, battery and counterweight each get a
separate slot. New area types OUTLAW_Helmet_BRS / OUTLAW_Helmet_Counterweight (OUTLAW_Helmet_Battery keeps the BNVD battery pack
and the ShawBrain battery pouches). The slots are added to the SF base prefab (Bump + Ballistic inherit it), then every
Maritime / XP helmet prefab is re-derived from the SF base exactly the way gen_maritime.py / gen_xp.py derive it (same ids,
same meshes and rails), so the XP gets Earpro and Scrims back. Only prefab / script text is written: no asset or meta is
touched, so Workbench has nothing to reimport.
"""
import difflib, glob, os, re

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])

SF_BASE = "Prefabs/Helmets/SF V2 Helmets/SF_Helmet_AOR1 (base dont touch).et"
NEW_AREAS = [("BRS", "OUTLAW_Helmet_BRS"), ("Counterweight", "OUTLAW_Helmet_Counterweight")]
AREA_OF = {"Prefabs/Batteries/PVS-31 BRS (MC).et": "OUTLAW_Helmet_BRS",
           "Prefabs/Batteries/OpsCore Counterweight (Coyote).et": "OUTLAW_Helmet_Counterweight"}
SLOTS_TEXT = "Removable rails, ear pro, BRS, battery, counterweight, scrim, NVG, light and strobe slots."

sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
for c in ("// Helmet rails (removable part of the modular SF V2 helmets)\n",
          "// Ops-Core Maritime rails (removable part of the Maritime helmets)\n",
          "// Ops-Core FAST XP rails (removable part of the XP / XP Carbon helmets)\n"):
    sc = sc.replace(c, "")
for _, area in NEW_AREAS:
    if f"class {area}:" not in sc:
        sc = sc.rstrip() + f"\n\nclass {area}: LoadoutAreaType{{}};\n"
write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc)

for p, area in AREA_OF.items():
    t = read(p)
    write(p, re.sub(r"AreaType OUTLAW_Helmet_Battery ", f"AreaType {area} ", t, count=1))

base = read(SF_BASE)
if "LoadoutSlotInfo BRS" not in base:
    blocks = "".join(f'    LoadoutSlotInfo {name} {{\n     InheritParentSkeleton 1\n'
                     f'     AreaType {area} "{{{guid("c:base:area_" + name.lower())}}}" {{\n     }}\n    }}\n'
                     for name, area in NEW_AREAS)
    m = re.search(r"    LoadoutSlotInfo Battery \{\n(?:     .*\n)*?    \}\n", base)
    base = base[:m.end()] + blocks + base[m.end():]
base = re.sub(r'(ClothNodeStorageComponent[\s\S]*?Description )"Modular SF V2 Bump helmet\.[^"]*"',
              lambda m: m.group(1) + '"Modular SF V2 Bump helmet. ' + SLOTS_TEXT + '"', base, count=1)
write(SF_BASE, base)


def derive(p, model, rail_area):
    """gen_maritime.py / gen_xp.py helmet transform of the SF base, meshes + rails taken from the current prefab."""
    cur = read(p)
    item = re.search(r'ItemModel "([^"]*)"', cur).group(1)
    worn = re.search(r'WornModel "([^"]*)"', cur).group(1)
    rails = re.search(r'LoadoutSlotInfo Rails \{\s*Prefab "([^"]*)"', cur).group(1)
    pretty = re.search(r'InventoryItemComponent[\s\S]*?Name "[^"(]*\(([^)]*)\)"', cur).group(1)
    t = base
    t = re.sub(r'(?m)^ ID "[0-9A-F]{16}"', f' ID "{guid("id:" + p)}"', t, count=1)
    t = re.sub(r'"\{([0-9A-F]{16})\}"', lambda m: '"{%s}"' % guid(f"c:{p}:{m.group(1)}"), t)
    t = re.sub(r'(MeshObject "\{[0-9A-F]{16}\}" \{\s*Object )"[^"]*"', lambda m: m.group(1) + f'"{item}"', t, count=1)
    t = re.sub(r'WornModel "[^"]*"', f'WornModel "{worn}"', t)
    t = re.sub(r'ItemModel "[^"]*"', f'ItemModel "{item}"', t)
    t = re.sub(r'(LoadoutSlotInfo Rails \{\s*Prefab )"[^"]*"', lambda m: m.group(1) + f'"{rails}"', t)
    t = t.replace("AreaType OUTLAW_Helmet_Rails ", f"AreaType {rail_area} ")
    if rail_area == "OUTLAW_Helmet_MaritimeRails":
        for _o, _n in {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_MaritimeEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_MaritimeBRS", "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_MaritimeBattery"}.items():
            t = t.replace(f"AreaType {_o} ", f"AreaType {_n} ")
    if rail_area == "OUTLAW_Helmet_XPRails":
        for _o, _n in {"OUTLAW_Helmet_EarPro": "OUTLAW_Helmet_XPEarPro", "OUTLAW_Helmet_BRS": "OUTLAW_Helmet_XPBRS", "OUTLAW_Helmet_Battery": "OUTLAW_Helmet_XPBattery", "OUTLAW_Helmet_Counterweight": "OUTLAW_Helmet_XPCounterweight", "OUTLAW_Helmet_Scrim": "OUTLAW_Helmet_XPScrim"}.items():
            t = t.replace(f"AreaType {_o} ", f"AreaType {_n} ")
    t = re.sub(r'(ClothNodeStorageComponent[\s\S]*?Name )"[^"]*"(\s*Description )"[^"]*"',
               lambda m: m.group(1) + f'"{model} ({pretty})"' + m.group(2) + f'"Modular {model} helmet. {SLOTS_TEXT}"', t, count=1)
    t = re.sub(r'(InventoryItemComponent[\s\S]*?Name )"[^"]*"', lambda m: m.group(1) + f'"{model} ({pretty})"', t, count=1)
    return cur, t


XP_MODELS = {"XP3": "Ops-Core FAST XP", "XP4": "Ops-Core FAST XP 4-Hole", "XPC3": "Ops-Core FAST XP Carbon",
             "XPC4": "Ops-Core FAST XP Carbon 4-Hole"}
jobs = [(p, "Ops-Core Maritime", "OUTLAW_Helmet_MaritimeRails")
        for p in sorted(glob.glob(ADDON + "Prefabs/Helmets/Maritime/Maritime_Helmet_*.et"))]
jobs += [(p, XP_MODELS[os.path.basename(p).split("_")[0]], "OUTLAW_Helmet_XPRails")
         for p in sorted(glob.glob(ADDON + "Prefabs/Helmets/XP/XP*_Helmet_*.et"))]
added = {}
for full, model, rail_area in jobs:
    p = full[len(ADDON):].replace("\\", "/")
    cur, t = derive(p, model, rail_area)
    plus = [l for l in difflib.ndiff(cur.splitlines(), t.splitlines()) if l.startswith("+ ")]
    minus = [l for l in difflib.ndiff(cur.splitlines(), t.splitlines()) if l.startswith("- ")]
    bad = [l for l in minus if "Description" not in l]
    if bad:
        raise SystemExit(f"{p}: re-derive would remove lines {bad[:5]}")
    write(p, t)
    added[p] = sorted(set(re.findall(r"LoadoutSlotInfo (\w+)", "\n".join(plus))))
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
for p, s in added.items():
    print(os.path.basename(p), s)
print("prefabs", len(added))
