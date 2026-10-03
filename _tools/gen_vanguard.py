"""Vanguard-Night Vision Systems integration for OUTLAW helmets (user 2026-10-02: "build into OUTLAW", "put them into the
slots already there"). OUTLAW depends on Vanguard (6F417A32E17A2178) and:
- moves the existing NVG / HelStroke slots of the SF, Maritime and XP helmets to the seats Vanguard measured on the SF
  shell (Vanguard's test helmet was a copy of this helmet, same Head frame);
- overrides Vanguard's NVG base, strobe base and both battery prefabs (same path + GUID + root ID, diff only) so they
  use OUTLAW_Helmet_NVG / OUTLAW_Helmet_Strobe / OUTLAW_Helmet_Battery;
- gives the battery an OUTLAW-style skinned worn model (build_vnvs_battery.py) because OUTLAW's battery slots carry no
  offset, plus (Maritime) / (XP) battery variants like the BNVD pack, and catalogs those variants.
Re-runnable: every write is idempotent.
"""
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SFHELMETS")
VN = "D:/Projects/Vanguard-Night-Vision-Systems"
VANGUARD_GUID = "6F417A32E17A2178"

NVG_OFFSET = {"SF": "-0.0021 0.1365 -0.1213", "Maritime": "-0.0021 0.1302 -0.1230", "XP": "-0.0021 0.1278 -0.1225"}
NVG_ANGLES = "0 -179.996 0"
STROBE_OFFSET = {"SF": "0.0001 0.1748 0.0768", "Maritime": "0.0001 0.1727 0.0768", "XP": "0.0001 0.1708 0.0768"}
STROBE_ANGLES = "0 -179.996 0"

HELMETS = ["Prefabs/Helmets/SF V2 Helmets/SF_Helmet_AOR1 (base dont touch).et",
           "Prefabs/Helmets/Maritime/Maritime_Helmet.et",
           "Prefabs/Helmets/XP/XP_Helmet.et"]

BATTERY_XOB_GUID = "0CAE98DE16346B85"
BATTERY_XOB = "ASSETS/Helmet Accessories/GPNVG18 BATTERY/vnvs_gpnvg18_battery.xob"
BLACK_EMAT = "{C7DE330FA849945E}Assets/NVG/GPNVG18/Data/VNVS_GPNVG18_Black.emat"
TAN_EMAT = "{D1FBF60036CF64B8}Assets/NVG/GPNVG18/Data/VNVS_GPNVG18_Tan.emat"

OVERRIDES = {
    "Prefabs/NVG/VNVS_NVG_Base.et": ("CF2F6A043B09D89C", "OUTLAW_Helmet_NVG", "096F09E4684E9FC6", None),
    "Prefabs/Strobes/VNVS_Strobe_Base.et": ("FC3B5736B7FA1590", "OUTLAW_Helmet_Strobe", "7679563EF2796C3E", None),
    "Prefabs/NVG/VNVS_GPNVG18_Battery_Black.et": ("6C9BA7957B908E6E", "OUTLAW_Helmet_Battery", "6F413CFA2E067B63", BLACK_EMAT),
    "Prefabs/NVG/VNVS_GPNVG18_Battery_Tan.et": ("B05C0BAA22B29963", "OUTLAW_Helmet_Battery", "AA830A19ADD4C2C5", TAN_EMAT),
}

BASE_BATTERY = {"Black": "{03F2275CAE887ABC}Prefabs/NVG/VNVS_GPNVG18_Battery_Black.et",
                "Tan": "{1C66C86F3B92336A}Prefabs/NVG/VNVS_GPNVG18_Battery_Tan.et"}

VARIANTS = [
    ("Black", "Maritime", "OUTLAW_Helmet_MaritimeBattery", "6485B02BAD3A28F1", "2725C5703FF7214F", "E467EF72FCA72AD2", "8DBF0C8C7F64D29C", "A0121CC2668E64FC"),
    ("Black", "XP", "OUTLAW_Helmet_XPBattery", "602A497BC2BD63BC", "03E367F2D2264519", "F60006D318EC40EF", "FB1ECDBDD2296EFB", "64C6F8C5FEE78E6D"),
    ("Tan", "Maritime", "OUTLAW_Helmet_MaritimeBattery", "402409E9033B0579", "883898411F855389", "4393D13EF91928E2", "02BB57C48C910D85", "D18BA672D045ABAA"),
    ("Tan", "XP", "OUTLAW_Helmet_XPBattery", "A95EFFF95868D869", "5E1A8E9B905661BA", "56BA4A726B9581D9", "8F625C9F1843A962", "C01BD2B8A4D78A1E"),
]

CATALOG = "Configs/EntityCatalog/US/InventoryItems_EntityCatalog_US.conf"
PLATFORMS = ["XBOX_ONE", "XBOX_SERIES", "PS4", "PS5", "HEADLESS"]


def path(rel):
    return os.path.join(ROOT, rel)


def read(rel):
    return open(path(rel), encoding="utf-8", newline="").read()


def write(rel, text):
    os.makedirs(os.path.dirname(path(rel)), exist_ok=True)
    open(path(rel), "w", encoding="utf-8", newline="\n").write(text)


def entity_meta(guid, rel):
    lines = ["MetaFileClass {", f' Name "{{{guid}}}{rel}"', " Configurations {", "  EntityTemplateResourceClass PC {", "  }"]
    lines += [f"  EntityTemplateResourceClass {p} : PC {{\n  }}" for p in PLATFORMS]
    lines += [" }", "}", ""]
    return "\n".join(lines)


def gproj():
    s = read("addon.gproj")
    if VANGUARD_GUID in s:
        return
    s2 = re.sub(r"(Dependencies \{\s*\n)(\s*)", lambda m: m.group(1) + m.group(2) + f'"{VANGUARD_GUID}"\n' + m.group(2), s, count=1)
    if s2 == s:
        raise SystemExit("could not add the Vanguard dependency to addon.gproj")
    write("addon.gproj", s2)


def set_slot(text, slot, offset, angles):
    pattern = re.compile(r"(LoadoutSlotInfo " + slot + r" \{\n(?:\s+PivotID \"[^\"]*\"\n)?)((?:\s+Offset [^\n]*\n)?)((?:\s+Angles [^\n]*\n)?)")
    m = pattern.search(text)
    if not m:
        raise SystemExit("slot not found: " + slot)
    indent = re.match(r"\s*", m.group(1).split("\n")[1] if "\n" in m.group(1) else "     ").group(0) or "     "
    head = m.group(1)
    if "PivotID" not in head:
        head += f'{indent}PivotID "Head"\n'
    return text[:m.start()] + head + f"{indent}Offset {offset}\n{indent}Angles {angles}\n" + text[m.end():]


def helmets():
    for rel in HELMETS:
        s = read(rel)
        family = "XP" if "/XP/" in rel else "Maritime" if "/Maritime/" in rel else "SF"
        s = set_slot(s, "NVG", NVG_OFFSET[family], NVG_ANGLES)
        s = set_slot(s, "HelStroke", STROBE_OFFSET[family], STROBE_ANGLES)
        write(rel, s)


def overrides():
    for rel, (root_id, area, area_guid, emat) in OVERRIDES.items():
        comp = [f'   AreaType {area} "{{{area_guid}}}" {{', "   }"]
        if emat:
            comp += [f'   WornModel "{{{BATTERY_XOB_GUID}}}{BATTERY_XOB}"', "   WornMaterialsOverride {", f'    "{emat}"', "   }"]
        body = ['GenericEntity : "{E3FF2D4B510769C1}Prefabs/Characters/Core/Eyewear_base.et" {', f' ID "{root_id}"',
                " components {", '  BaseLoadoutClothComponent "{559C7E9ADCAE6DFF}" {'] + comp + ["  }", " }", "}", ""]
        write(rel, "\n".join(body))
        meta = open(os.path.join(VN, rel + ".meta"), encoding="utf-8").read()
        write(rel + ".meta", meta)


def battery_meta():
    bnvd = read("ASSETS/Helmet Accessories/BNVD BATTERY/bnvdbattery.xob.meta")
    s = bnvd.replace('{A9601CD467097E4A}ASSETS/Helmet Accessories/BNVD BATTERY/bnvdbattery.xob', f"{{{BATTERY_XOB_GUID}}}{BATTERY_XOB}")
    s = re.sub(r'SourceMaterial "[^"]*"', 'SourceMaterial "VNVS_GPNVG18_Battery"', s, count=1)
    s = re.sub(r'AssignedMaterial "[^"]*"', f'AssignedMaterial "{BLACK_EMAT}"', s, count=1)
    s = re.sub(r'MeshParam "[^"]*"', 'MeshParam "VNVS_GPNVG18_Battery_OUTLAW"', s, count=1)
    write(BATTERY_XOB + ".meta", s)


def variants():
    entries = []
    for colour, family, area, guid, root_id, area_guid, cat_entry, cat_data in VARIANTS:
        rel = f"Prefabs/Batteries/GPNVG-18 Battery Pack ({colour}) ({family}).et"
        body = [f'GenericEntity : "{BASE_BATTERY[colour]}" {{', f' ID "{root_id}"', " components {",
                '  BaseLoadoutClothComponent "{559C7E9ADCAE6DFF}" {', f'   AreaType {area} "{{{area_guid}}}" {{', "   }", "  }",
                '  InventoryItemComponent "{559C7E9ADCAE6DD3}" {', '   Attributes ItemAttributeCollection "{559C7E9ADCAE6DCD}" {',
                '    ItemDisplayName UIInfo "{559C7E9ADCAE6DCF}" {', f'     Name "GPNVG-18 Battery Pack ({colour}) ({family})"',
                "    }", "   }", "  }", " }", "}", ""]
        write(rel, "\n".join(body))
        write(rel + ".meta", entity_meta(guid, rel))
        entries.append((cat_entry, cat_data, f"{{{guid}}}{rel}"))
    return entries


def catalog(entries):
    s = read(CATALOG)
    anchor = s.find("BNVD Battery Pack (Maritime).et")
    if anchor < 0:
        raise SystemExit("catalog anchor missing")
    start = s.rfind("SCR_EntityCatalogInventoryItem", 0, anchor)
    indent = s[s.rfind("\n", 0, start) + 1:start]
    add = ""
    for cat_entry, cat_data, prefab in entries:
        if prefab.split("}", 1)[1] in s:
            continue
        add += (f'{indent}SCR_EntityCatalogInventoryItem "{{{cat_entry}}}" {{\n{indent} m_sEntityPrefab "{prefab}"\n'
                f'{indent} m_aEntityDataList {{\n{indent}  SCR_ArsenalItem "{{{cat_data}}}" {{\n{indent}   m_eItemType EQUIPMENT\n'
                f'{indent}  }}\n{indent} }}\n{indent}}}\n')
    if add:
        line_start = s.rfind("\n", 0, start) + 1
        s = s[:line_start] + add + s[line_start:]
        write(CATALOG, s)


gproj()
helmets()
overrides()
battery_meta()
catalog(variants())
print("VANGUARD INTEGRATION OK")
