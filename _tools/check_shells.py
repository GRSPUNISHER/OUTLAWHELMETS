"""Offline gate for the interchangeable shells (python _tools/check_shells.py): every helmet / shell / rails prefab reference
resolves to a meta GUID with an existing file, every GRS area type is declared, every helmet has exactly one prefilled Shell
slot of its family and no armor of its own, every shell carries the armor + UTM hit zone, and the shells are in the catalog."""
import glob, os, re

A = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/SFHELMETS/"
guids = {}
for m in glob.glob(A + "**/*.meta", recursive=True):
    g = re.search(r'Name "\{([0-9A-F]{16})\}([^"]*)"', open(m, encoding="utf-8", errors="ignore").read())
    if g:
        guids[g.group(1)] = m[:-5]
classes = set(re.findall(r"class (\w+):", open(A + "Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c").read()))
FAM = {"SF V2 Helmets": "OUTLAW_Helmet_SFShell", "Maritime": "OUTLAW_Helmet_MaritimeShell", "XP": "OUTLAW_Helmet_XPShell"}
bad = 0


def refs_ok(p, t):
    global bad
    for g, rel in re.findall(r'"\{([0-9A-F]{16})\}((?:ASSETS|Prefabs)/[^"]+)"', t):
        if g not in guids or not os.path.exists(guids[g]):
            print("UNRESOLVED", os.path.relpath(p, A), g, rel); bad += 1
    for a in re.findall(r"AreaType (GRS_\w+) ", t):
        if a not in classes:
            print("NO CLASS", os.path.relpath(p, A), a); bad += 1


helmets = shells = 0
for fam, area in FAM.items():
    for p in glob.glob(A + f"Prefabs/Helmets/{fam}/*.et"):
        t = open(p, encoding="utf-8").read(); refs_ok(p, t); helmets += 1
        inherits = t.startswith("GameEntity :")
        if "SCR_ArmorDamageManagerComponent" in t:
            print("HELMET STILL ARMORED", os.path.basename(p)); bad += 1
        n = len(re.findall(r"LoadoutSlotInfo Shell \{", t))
        if n != 1:
            print("SHELL SLOTS", n, os.path.basename(p)); bad += 1
        sp = re.search(r'LoadoutSlotInfo Shell \{\s*Prefab "\{[0-9A-F]{16}\}([^"]+)"', t)
        if not sp or f"/{fam}/Shells/" not in sp.group(1):
            print("WRONG/NO SHELL PREFAB", os.path.basename(p), sp and sp.group(1)); bad += 1
        if not inherits and f"AreaType {area} " not in t:
            print("WRONG SHELL AREA", os.path.basename(p)); bad += 1
    for p in glob.glob(A + f"Prefabs/Helmets/{fam}/Shells/*.et"):
        t = open(p, encoding="utf-8").read(); refs_ok(p, t); shells += 1
        need = ["SCR_ArmorDamageManagerComponent", '"UTM_Helmet"', "PhysicsOnWearEnabled 1", f"AreaType {area} "]
        miss = [n for n in need if n not in t]
        if miss:
            print("SHELL MISSING", os.path.basename(p), miss); bad += 1
        worn = re.search(r'WornModel "\{([0-9A-F]{16})\}', t).group(1)
        if "UTM_Helmet" not in open(guids[worn] + ".meta", encoding="utf-8").read():
            print("SHELL XOB WITHOUT UTM", os.path.basename(p)); bad += 1
cat = open(A + "Configs/EntityCatalog/US/InventoryItems_EntityCatalog_US.conf", encoding="utf-8").read()
nc = [os.path.basename(p) for p in glob.glob(A + "Prefabs/Helmets/*/Shells/*.et") if os.path.basename(p) not in cat]
print("helmet prefabs", helmets, "shell prefabs", shells, "problems", bad, "shells not in catalog", nc)
