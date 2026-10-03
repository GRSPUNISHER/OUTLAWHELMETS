"""Offline gate for the XP attachments (python _tools/check_xp_acc.py): every resource an "(XP)" item or an XP helmet prefab
references resolves to a meta with that GUID and an existing file, every GRS area type is a declared class, every XP-only
slot has at least one item, and the catalog lists the items."""
import glob, os, re

A = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/SFHELMETS/"
guids = {}
for m in glob.glob(A + "**/*.meta", recursive=True):
    g = re.search(r'Name "\{([0-9A-F]{16})\}([^"]*)"', open(m, encoding="utf-8", errors="ignore").read())
    if g:
        guids[g.group(1)] = (g.group(2), m[:-5])
classes = set(re.findall(r"class (\w+):", open(A + "Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c").read()))
items = glob.glob(A + "Prefabs/**/*(XP).et", recursive=True)
helmets = glob.glob(A + "Prefabs/Helmets/XP/*.et")
bad = 0
item_areas, slot_areas = {}, set()
for p in items + helmets:
    t = open(p, encoding="utf-8").read()
    for g, rel in re.findall(r'"\{([0-9A-F]{16})\}((?:ASSETS|Prefabs)/[^"]+)"', t):
        if g not in guids:
            print("UNRESOLVED", os.path.basename(p), g, rel); bad += 1
        elif not os.path.exists(guids[g][1]):
            print("NO FILE", os.path.basename(p), guids[g][1]); bad += 1
    areas = re.findall(r"AreaType (GRS_\w+) ", t)
    for a in areas:
        if a not in classes:
            print("NO CLASS", os.path.basename(p), a); bad += 1
    if p in items:
        item_areas.setdefault(areas[0], []).append(os.path.basename(p))
    else:
        slot_areas.update(a for a in areas if "XP" in a)
for a in sorted(slot_areas):
    print(a, "<-", sorted(item_areas.get(a, [])) or "rails prefabs" if a == "OUTLAW_Helmet_XPRails" else sorted(item_areas.get(a, [])))
    if a != "OUTLAW_Helmet_XPRails" and not item_areas.get(a):
        print("EMPTY SLOT", a); bad += 1
cat = open(A + "Configs/EntityCatalog/US/InventoryItems_EntityCatalog_US.conf", encoding="utf-8").read()
missing = [os.path.basename(p) for p in items if os.path.basename(p) not in cat]
print("items", len(items), "helmets", len(helmets), "problems", bad, "not in catalog", missing)
