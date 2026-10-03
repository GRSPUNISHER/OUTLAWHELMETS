"""Place the exported FBXs into SFHELMETS and write every Workbench resource for the modular SF V2 helmets.

SUPERSEDED 2026-09-30 for helmet PREFABS: helmets are now one core + interchangeable shell per family, written by
gen_shells.py. Rerunning this script's helmet section brings back the old per-colour one-piece helmets.


  python _tools/gen_sf.py        (after build_sf.py and pack_textures.py)

Helmet = shell (Bump = vendor "Carbon", Ballistic = vendor "SF"; carries the UTM_Helmet hit zone) + prefilled
Rails slot part in the same colour + accessory slots. Colour = per-colour xob (each ASSETS/HELMET <C>/ folder keeps
its own SF.emat with the existing BCR/NMO). Existing prefab/xob GUIDs are kept so arsenals and loadouts still resolve.
GUIDs for new resources are stable in _tools/guids.json.
"""
import json, os, re, secrets, shutil, glob

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
ADDON = ROOT + "SFHELMETS/"
FBX = ROOT + "_tools/work/fbx/"
_GF = ROOT + "_tools/guids.json"
_G = json.load(open(_GF)) if os.path.exists(_GF) else {}
PLATFORMS = ("XBOX_ONE", "XBOX_SERIES", "PS4", "PS5", "HEADLESS")
TXO = {"PC": "{0877E7C4BB2B2C9A}Configs/System/ResourceTypes/PC/MeshObjectCommon.conf",
       "XBOX_ONE": "{9D5B6207F7628CE2}Configs/System/ResourceTypes/XBOX_ONE/MeshObjectCommon.conf",
       "XBOX_SERIES": "{DD9F02115C764647}Configs/System/ResourceTypes/XBOX_SERIES/MeshObjectCommon.conf",
       "PS4": "{53EC476BC921D99A}Configs/System/ResourceTypes/PS4/MeshObjectCommon.conf",
       "PS5": "{F62AA8E7B8EA9D26}Configs/System/ResourceTypes/PS5/MeshObjectCommon.conf",
       "HEADLESS": "{3A5B3356978039E8}Configs/System/ResourceTypes/HEADLESS/MeshObjectCommon.conf"}
TEX = {"BCR": {"PC": "{EAB5DE3219F9CBA8}Configs/System/ResourceTypes/PC/TextureColorMap.conf",
               "XBOX_ONE": "{91D862F89991BFBE}Configs/System/ResourceTypes/XBOX_ONE/TextureColorMap.conf",
               "XBOX_SERIES": "{5FEAED1642ECE679}Configs/System/ResourceTypes/XBOX_SERIES/TextureColorMap.conf",
               "PS4": "{12273E1A0928F0C4}Configs/System/ResourceTypes/PS4/TextureColorMap.conf",
               "PS5": "{531A0D167B1ABD97}Configs/System/ResourceTypes/PS5/TextureColorMap.conf",
               "HEADLESS": "{BEAF5CD0C438676E}Configs/System/ResourceTypes/HEADLESS/TextureColorMap.conf"},
       "NMO": {"PC": "{A968DA7F9A1E3A3E}Configs/System/ResourceTypes/PC/TextureNType.conf",
               "XBOX_ONE": "{7F6A4D372443A88D}Configs/System/ResourceTypes/XBOX_ONE/TextureNType.conf",
               "XBOX_SERIES": "{065D289C7FF8B20D}Configs/System/ResourceTypes/XBOX_SERIES/TextureNType.conf",
               "PS4": "{29DF4A6CBBABE916}Configs/System/ResourceTypes/PS4/TextureNType.conf",
               "PS5": "{DED3C8CA8494EA99}configs/ResourceTypes/PS5/TextureNType.conf",
               "HEADLESS": "{AFD658E4D0EB5FBC}Configs/System/ResourceTypes/HEADLESS/TextureNType.conf"}}
GM_BUMP = "{18C62B7F4A626E3B}Common/Materials/Game/Armor/armor_5mm.gamemat"
GM_BALLISTIC = "{CF50027087BA3402}Common/Materials/Game/PersonalProtection/hard_aramid_7.3mm.gamemat"
GM_ITEM = "{5EAA7FB0A83F90CF}Common/Materials/Game/plastic.gamemat"


def new_guid():
    g = secrets.token_hex(8).upper()
    while g in _G.values():
        g = secrets.token_hex(8).upper()
    return g


def guid(key):
    if key not in _G:
        _G[key] = new_guid()
    return _G[key]


def write(rel, text):
    full = ADDON + rel
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)


def read(rel):
    return open(ADDON + rel, encoding="utf-8").read()


def meta_guid(rel):
    """GUID of an existing resource from its .meta (None if the resource is new)."""
    p = ADDON + rel + ".meta"
    if not os.path.exists(p):
        return None
    return re.search(r'Name "\{([0-9A-F]{16})\}', open(p, encoding="utf-8").read()).group(1)


def rguid(rel):
    return meta_guid(rel) or guid("res:" + rel)


def ref(rel):
    return "{%s}%s" % (rguid(rel), rel)


def meta_name(rel):
    """Name line of an existing meta kept verbatim (some OUTLAW metas carry stale paths; GUID is what resolves)."""
    p = ADDON + rel + ".meta"
    if os.path.exists(p):
        return re.search(r'Name "([^"]+)"', open(p, encoding="utf-8").read()).group(1)
    return ref(rel)


def xob_meta(rel, materials, skinned, colliders=()):
    m = ['MetaFileClass {', f' Name "{meta_name(rel)}"', ' Configurations {', '  FBXResourceClass PC {']
    if skinned:
        m.append('   ExportSkinning 1')
    m.append('   MaterialAssigns {')
    for src, emat_ref in materials:
        m += [f'    MaterialAssignClass "{{{guid("ma:" + rel + ":" + src)}}}" {{', f'     SourceMaterial "{src}"',
              f'     AssignedMaterial "{emat_ref}"', '    }']
    m.append('   }')
    if colliders:
        m.append('   GeometryParams {')
        for name, preset, gm in colliders:
            m += [f'    GeometryParam {name} {{', f'     LayerPreset "{preset}"', '     SurfaceProperties {',
                  f'      "{gm}"', '     }', '     Mass 0', '     Margin 0', '    }']
        m.append('   }')
    m.append(f'   Common TXOCommonClass "{{{guid("txo:" + rel + ":PC")}}}" : "{TXO["PC"]}" {{')
    m += ['   }', '  }']
    for p in PLATFORMS:
        m += [f'  FBXResourceClass {p} : PC {{',
              f'   Common TXOCommonClass "{{{guid("txo:" + rel + ":" + p)}}}" : "{TXO[p]}" {{', '   }', '  }']
    m += [' }', '}', '']
    write(rel + ".meta", "\n".join(m))


def edds_meta(rel):
    kind = "NMO" if rel.endswith("_NMO.edds") else "BCR"
    m = ['MetaFileClass {', f' Name "{ref(rel)}"', ' Configurations {']
    for p in ("PC",) + PLATFORMS:
        m += [f'  PNGResourceClass {p} : "{TEX[kind][p]}" {{', '   MaxSize "2048"', '  }']
    m += [' }', '}', '']
    write(rel + ".meta", "\n".join(m))


def simple_meta(rel, cls):
    m = ['MetaFileClass {', f' Name "{ref(rel)}"', ' Configurations {', f'  {cls} PC {{', '  }']
    for p in PLATFORMS:
        m += [f'  {cls} {p} : PC {{', '  }']
    m += [' }', '}', '']
    write(rel + ".meta", "\n".join(m))


def emat(rel, bcr, nmo):
    write(rel, f'MatPBRBasic {{\n AllowUserAlphaBias 1\n DisableUserAphaInShadow 1\n BCRMap "{ref(bcr)}"\n NMOMap "{ref(nmo)}"\n}}\n')
    simple_meta(rel, "EMATResourceClass")


def existing_assigns(rel):
    """[(SourceMaterial, AssignedMaterial ref)] from an existing xob meta."""
    t = open(ADDON + rel + ".meta", encoding="utf-8").read()
    return re.findall(r'SourceMaterial "([^"]+)"\s*AssignedMaterial "([^"]+)"', t)


def place(part, rel_fbx, materials, utm_gm=None):
    """Copy the worn + _Item FBX of an exported part to rel_fbx (worn) and write both xob metas."""
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    shutil.copyfile(FBX + part + ".fbx", ADDON + rel_fbx)
    shutil.copyfile(FBX + part + "_Item.fbx", ADDON + item_fbx)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    xob_meta(worn, materials, True, [("UTM_Helmet", "FireGeo", utm_gm)] if utm_gm else [])
    xob_meta(item, materials, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    return worn, item


# ================================================================ helmets
# code, folder, pretty
COLOURS = [("AOR1", "HELMET AOR1", "AOR1"), ("MC", "HELMET MC", "MC"), ("MCB", "HELMET BLACK", "MCB"),
           ("ODGreen", "HELMET GREEN", "OD Green"), ("RG", "HELMET RG", "RG"), ("Tan", "HELMET TAN", "Tan")]
PF = "Prefabs/Helmets/SF V2 Helmets/"
BASE = PF + "SF_Helmet_AOR1 (base dont touch).et"
BASE_REF = "{AF457DB4423C4107}" + BASE

# The Ballistic has its OWN textures (install_ballistic_textures.py: the user's MCB HELMET.spp stack applied in Painter);
# the Bump's SF.emat / SF_*_BCR/NMO are the user's finished Bump textures and are never written.
BALLISTIC_PREFIX = {"HELMET AOR1": "AOR1SF", "HELMET BLACK": "mcbSF", "HELMET GREEN": "grSF", "HELMET MC": "SF",
                    "HELMET RG": "RGSF", "HELMET TAN": "tanSF"}

xobs = {}
for code, folder, _ in COLOURS:
    sf_emat = meta_name(f"ASSETS/{folder}/Data/SF.emat")
    mats = [("SF", sf_emat)]
    d = f"ASSETS/{folder}/Data/"
    bal_bcr, bal_nmo = d + BALLISTIC_PREFIX[folder] + "Ballistic_BCR.edds", d + BALLISTIC_PREFIX[folder] + "Ballistic_NMO.edds"
    edds_meta(bal_bcr); edds_meta(bal_nmo)
    emat(d + "SFBallistic.emat", bal_bcr, bal_nmo)
    bal_mats = [("SF", ref(d + "SFBallistic.emat"))]
    xobs[code] = {
        "Bump": place("SF_Bump", f"ASSETS/{folder}/SF V2 Bump.fbx", mats, GM_BUMP),
        "Ballistic": place("SF_Ballistic", f"ASSETS/{folder}/SF V2 Ballistic.fbx", bal_mats, GM_BALLISTIC),
        "Rails": place("SF_Rails", f"ASSETS/{folder}/SF V2 Rails.fbx", mats),
    }
    for old in glob.glob(ADDON + f"ASSETS/{folder}/SF V2 Bump (Rigged).*"):
        os.remove(old)

# ================================================================ accessories
ACC = "ASSETS/Helmet Accessories/"
EXISTING_ACC = {   # part -> [(existing fbx, prefab)]
    "SM_PVS31_BRS": [(ACC + "BATTERYPACK/batterypack.fbx", "Prefabs/Batteries/PVS-31 BRS (MC).et")],
    "SM_PeltorComtac_VII_ARC": [(ACC + "COMTACS/RG COMTACS/comtacviinostrap.fbx", "Prefabs/EarPro/Comtacs (RG).et"),
                                (ACC + "COMTACS/TAN COMTACS/comtacviinostrap.fbx", "Prefabs/EarPro/Comtacs (Tan).et")],
    "High_Cut_Helmet_Scrim_Oak": [(ACC + "Scrims/HighCut Oak MC/HighCut Scrim Oak.fbx", "Prefabs/Scrims/HighCut Oak Scrim (MC).et"),
                                  (ACC + "Scrims/HighCut Ranger Green/HighCut Scrim Oak.fbx", "Prefabs/Scrims/HighCut Oak Scrim (RG).et")],
    "High_Cut_Helmet_Scrim_SemiCircle": [(ACC + "Scrims/HighCut Semi MC/HighCut Scrim Oak.fbx", "Prefabs/Scrims/HighCut SemiCircle Scrim (MC).et"),
                                         (ACC + "Scrims/HighCut Semi RG/HighCut Scrim Oak.fbx", "Prefabs/Scrims/HighCut SemiCircle Scrim (RG).et")],
}
acc_models = {}
for part, entries in EXISTING_ACC.items():
    for rel_fbx, prefab in entries:
        mats = existing_assigns(rel_fbx[:-4] + ".xob")
        acc_models[prefab] = place(part, rel_fbx, mats)

# new: part -> (folder, fbx stem, source material, texture stem, prefab, name, area)
NEW_ACC = {
    "OpsCore_AMP": ("AMP", "OpsCore_AMP", "MI_Ops_Core_AMP_Headset", "OpsCore_AMP", "Prefabs/EarPro/OpsCore AMP.et",
                    "Ops-Core AMP", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    "SM_Comtac_6_ARC": ("COMTACS/COMTAC VI", "comtacvi", "MI_Comtac_6", "Comtac6", "Prefabs/EarPro/Comtac VI.et",
                        "Comtac VI", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    "NVG_Counterweight_OpsCore_Kit": ("COUNTERWEIGHT", "counterweight", "MI_NVG_Counterweight_OpsCore_Kit_Coyote",
                                      "OpsCoreCounterweight_Coyote", "Prefabs/Batteries/OpsCore Counterweight (Coyote).et",
                                      "Ops-Core Counterweight (Coyote)", "Helmet Attachment", "OUTLAW_Helmet_Counterweight"),
    "BNVDFBat": ("BNVD BATTERY", "bnvdbattery", "BNVDFBat", "BNVDFBat", "Prefabs/Batteries/BNVD Battery Pack.et",
                 "BNVD Battery Pack", "Helmet Attachment", "OUTLAW_Helmet_Battery"),
}
for part, (folder, stem, srcmat, tex, prefab, *_rest) in NEW_ACC.items():
    d = f"{ACC}{folder}/Data/"
    bcr, nmo = d + tex + "_BCR.edds", d + tex + "_NMO.edds"
    edds_meta(bcr); edds_meta(nmo)
    em = d + srcmat + ".emat"
    emat(em, bcr, nmo)
    acc_models[prefab] = place(part, f"{ACC}{folder}/{stem}.fbx", [(srcmat, ref(em))])

# ================================================================ slot type
sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
for _a in ("OUTLAW_Helmet_Rails", "OUTLAW_Helmet_BRS", "OUTLAW_Helmet_Counterweight"):
    if f"class {_a}:" not in sc:
        sc = sc.rstrip() + f"\n\nclass {_a}: LoadoutAreaType{{}};\n"
write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc)

# ================================================================ accessory prefabs
SND_PICK = "{0026043E3CD828D0}Sounds/Items/_SharedData/PickUp/Items_PickUp_Generic_Metallic.acp"
SND_DROP = "{7F55C292FBA55048}Sounds/Items/_SharedData/Drop/Items_Drop_Generic_Metallic.acp"


def top_components(rel):
    """{component class: GUID} of an existing root prefab, so rewritten prefabs keep their component ids."""
    if not os.path.exists(ADDON + rel):
        return {}
    return dict(re.findall(r'^  (\w+) "\{([0-9A-F]{16})\}" \{', read(rel), re.M))


def accessory_prefab(rel, name, desc, area, worn, item, entity_id=None, fp_hide=True):
    old = top_components(rel)
    k = "c:" + rel + ":"
    c = lambda n: "{%s}" % (old.get(n) or guid(k + n))
    n = lambda n: "{%s}" % guid(k + n)
    eid = entity_id or (re.search(r'ID "([0-9A-F]{16})"', read(rel)).group(1) if os.path.exists(ADDON + rel) else guid("id:" + rel))
    fp = f'  OUTLAW_FirstPersonHideComponent "{c("OUTLAW_FirstPersonHideComponent")}" {{\n  }}\n' if fp_hide else ""
    t = f'''GenericEntity {{
 ID "{eid}"
 components {{
  ParametricMaterialInstanceComponent "{c("ParametricMaterialInstanceComponent")}" {{
   UserParamAlpha 0
  }}
  Persistence "{c("Persistence")}" {{
  }}
{fp}  InventoryItemComponent "{c("InventoryItemComponent")}" {{
   Attributes SCR_ItemAttributeCollection "{n("attr")}" {{
    ItemDisplayName UIInfo "{n("ui")}" {{
     Name "{name}"
     Description "{desc}"
    }}
    ItemPhysAttributes ItemPhysicalAttributes "{n("phys")}" {{
     SizeSetupStrategy Manual
     ItemVolume 10
    }}
    CustomAttributes {{
     PreviewRenderAttributes "{n("prev")}" {{
      CameraOrbitAngles -25 30 0
      CameraDistanceToItem 1
      FOV 10
     }}
    }}
   }}
  }}
  MeshObject "{c("MeshObject")}" {{
   Object "{ref(item)}"
  }}
  RigidBody "{c("RigidBody")}" {{
   Mass 0.3
   LinearDamping 0.2
   AngularDamping 0.4
   SimState None
   ModelGeometry 1
  }}
  SCR_SoundDataComponent "{c("SCR_SoundDataComponent")}" {{
   m_aAudioSourceConfiguration {{
    SCR_AudioSourceConfiguration "{n("snd1")}" {{
     m_sSoundProject "{SND_PICK}"
     m_sSoundEventName "SOUND_PICK_UP"
    }}
    SCR_AudioSourceConfiguration "{n("snd2")}" {{
     m_sSoundProject "{SND_PICK}"
     m_sSoundEventName "SOUND_EQUIP"
     m_eFlags 0
    }}
    SCR_AudioSourceConfiguration "{n("snd3")}" {{
     m_sSoundProject "{SND_DROP}"
     m_sSoundEventName "SOUND_DROP"
    }}
   }}
  }}
  BaseLoadoutClothComponent "{c("BaseLoadoutClothComponent")}" {{
   AreaType {area} "{n("area")}" {{
   }}
   WornModel "{ref(worn)}"
   ItemModel "{ref(item)}"
  }}
  ActionsManagerComponent "{c("ActionsManagerComponent")}" {{
   ActionContexts {{
    UserActionContext "{n("ctx")}" {{
     UIInfo SCR_ActionContextUIInfo "{n("ctxui")}" {{
     }}
     ContextName "default"
     Position PointInfo "{n("ctxp")}" {{
     }}
     Radius 0.3
    }}
   }}
   additionalActions {{
    SCR_PickUpItemAction "{n("pick")}" {{
     ParentContextList {{
      "default"
     }}
     UIInfo SCR_ActionUIInfo "{n("pickui")}" {{
      Name "#AR-Inventory_PickUp"
      m_sIconName "pick-up"
     }}
    }}
   }}
  }}
  NwkPhysicsMovementComponent "{c("NwkPhysicsMovementComponent")}" {{
  }}
  RplComponent "{c("RplComponent")}" {{
   "Rpl State Override" Runtime
   "Parent Node From Parent Entity" 0
  }}
  Hierarchy "{c("Hierarchy")}" {{
  }}
 }}
}}
'''
    write(rel, t)
    if not os.path.exists(ADDON + rel + ".meta"):
        simple_meta(rel, "EntityTemplateResourceClass")


ACC_INFO = {
    "Prefabs/Batteries/PVS-31 BRS (MC).et": ("PVS-31 BRS (MC)", "Helmet Attachment", "OUTLAW_Helmet_BRS"),
    "Prefabs/EarPro/Comtacs (RG).et": ("Comtac VII (RG)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    "Prefabs/EarPro/Comtacs (Tan).et": ("Comtac VII (Tan)", "Ear Pro", "OUTLAW_Helmet_EarPro"),
    "Prefabs/Scrims/HighCut Oak Scrim (MC).et": ("HighCut Oak Scrim (MC)", "Helmet Attachment", "OUTLAW_Helmet_Scrim"),
    "Prefabs/Scrims/HighCut Oak Scrim (RG).et": ("HighCut Oak Scrim (RG)", "Helmet Attachment", "OUTLAW_Helmet_Scrim"),
    "Prefabs/Scrims/HighCut SemiCircle Scrim (MC).et": ("HighCut SemiCircle Scrim (MC)", "Helmet Attachment", "OUTLAW_Helmet_Scrim"),
    "Prefabs/Scrims/HighCut SemiCircle Scrim (RG).et": ("HighCut SemiCircle Scrim (RG)", "Helmet Attachment", "OUTLAW_Helmet_Scrim"),
}
for part, (folder, stem, srcmat, tex, prefab, name, desc, area) in NEW_ACC.items():
    ACC_INFO[prefab] = (name, desc, area)
for prefab, (name, desc, area) in ACC_INFO.items():
    accessory_prefab(prefab, name, desc, area, *acc_models[prefab])

# Shaw Brain pouches are not in the .blend: models untouched, prefab bugs fixed
for col in ("MC", "RG"):
    p = f"Prefabs/Battery Pouches/ShawBrainPouch ({col}).et"
    xob = re.search(r'Object "\{[0-9A-F]{16}\}([^"]+)"', read(p)).group(1)
    accessory_prefab(p, f"ShawBrain Pouch ({col})", "Helmet Attachment", "OUTLAW_Helmet_Battery", xob, xob)

# ================================================================ rails prefabs
rails_prefab = {}
for code, folder, pretty in COLOURS:
    p = f"{PF}Rails/SF_Rails_{code}.et"
    accessory_prefab(p, f"SF V2 ARC Rails ({pretty})", "Removable ARC rails for the SF V2 Bump / Ballistic helmets.",
                     "OUTLAW_Helmet_Rails", *xobs[code]["Rails"])
    rails_prefab[code] = p

# ================================================================ helmet prefabs
base = read(BASE)
worn, item = xobs["AOR1"]["Bump"]
base = re.sub(r'(ClothNodeStorageComponent[\s\S]*?Name )"[^"]*"(\s*Description )"[^"]*"',
              r'\1"SF V2 Bump (AOR1)"\2"Modular SF V2 Bump helmet. Removable rails, ear pro, BRS, battery, counterweight, scrim, NVG, light and strobe slots."',
              base, count=1)
base = re.sub(r'(InventoryItemComponent[\s\S]*?Name )"[^"]*"', r'\1"SF V2 Bump (AOR1)"', base, count=1)
base = re.sub(r'(MeshObject "\{[0-9A-F]{16}\}" \{\s*Object )"[^"]*"', r'\1"%s"' % ref(item), base, count=1)
base = re.sub(r'WornModel "[^"]*"', 'WornModel "%s"' % ref(worn), base)
base = re.sub(r'ItemModel "[^"]*"', 'ItemModel "%s"' % ref(item), base)
base = base.replace('"UTM_Helmet_PASGT_01"', '"UTM_Helmet"')
if "LoadoutSlotInfo Rails" not in base:
    rails_slot = (f'    LoadoutSlotInfo Rails {{\n     Prefab "{ref(rails_prefab["AOR1"])}"\n     InheritParentSkeleton 1\n'
                  f'     AreaType OUTLAW_Helmet_Rails "{{{guid("c:base:area_rails")}}}" {{\n     }}\n    }}\n')
    base = base.replace("   Slots {\n", "   Slots {\n" + rails_slot, 1)
else:
    base = re.sub(r'(LoadoutSlotInfo Rails \{\s*Prefab )"[^"]*"', r'\1"%s"' % ref(rails_prefab["AOR1"]), base)
if "LoadoutSlotInfo BRS" not in base:
    _m = re.search(r"    LoadoutSlotInfo Battery \{\n(?:     .*\n)*?    \}\n", base)
    base = base[:_m.end()] + "".join(
        f'    LoadoutSlotInfo {n} {{\n     InheritParentSkeleton 1\n'
        f'     AreaType {a} "{{{guid("c:base:area_" + n.lower())}}}" {{\n     }}\n    }}\n'
        for n, a in (("BRS", "OUTLAW_Helmet_BRS"), ("Counterweight", "OUTLAW_Helmet_Counterweight"))) + base[_m.end():]
if "ShowAllChildrens" not in base:
    base = base.replace("      FOV 65\n", "      FOV 65\n      ShowAllChildrens 1\n", 1)
write(BASE, base)


def child(rel, name, worn, item, rails):
    t = f'''GameEntity : "{BASE_REF}" {{
 ID "6A2F5CA9A0962B93"
 components {{
  ClothNodeStorageComponent "{{6A2F5CA924199E9D}}" {{
   Attributes SCR_ItemAttributeCollection "{{6A2F5CA9DDAB18D2}}" {{
    ItemDisplayName UIInfo "{{6A2F5CA9D6676EE3}}" {{
     Name "{name}"
    }}
   }}
  }}
  InventoryItemComponent "{{6A2F5CA9179317BC}}" {{
   Attributes SCR_ItemAttributeCollection "{{6A2F5CA91793164B}}" {{
    ItemDisplayName UIInfo "{{6A2F5CA917931623}}" {{
     Name "{name}"
    }}
   }}
  }}
  MeshObject "{{6A2F5CA91793117D}}" {{
   Object "{ref(item)}"
  }}
  BaseLoadoutClothComponent "{{6A2F5CA91793174C}}" {{
   Slots {{
    LoadoutSlotInfo Rails {{
     Prefab "{ref(rails)}"
    }}
   }}
   WornModel "{ref(worn)}"
   ItemModel "{ref(item)}"
  }}
 }}
}}
'''
    write(rel, t)
    if not os.path.exists(ADDON + rel + ".meta"):
        simple_meta(rel, "EntityTemplateResourceClass")


helmets = []
for code, folder, pretty in COLOURS:
    bump = PF + ("SF_Helmet_AOR1 .et" if code == "AOR1" else f"SF_Helmet_{code}.et")
    if code != "AOR1":
        child(bump, f"SF V2 Bump ({pretty})", *xobs[code]["Bump"], rails_prefab[code])
    ball = f"{PF}SF_Ballistic_Helmet_{code}.et"
    child(ball, f"SF V2 Ballistic ({pretty})", *xobs[code]["Ballistic"], rails_prefab[code])
    helmets += [bump, ball]

# ================================================================ catalog
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
    add = "".join(cat_entry(p, kind) for p in prefabs if "{%s}" % rguid(p) not in text)
    return text[:j] + add + text[j:]


cat = add_to_list(cat, "Outlaw Helmets", [h for h in helmets if "Ballistic" in h], "HEADWEAR")
cat = add_to_list(cat, "Outlaw Helmet Accesories",
                  list(rails_prefab.values()) + [v[4] for v in NEW_ACC.values()], "EQUIPMENT")
write(CAT, cat)

json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
print("helmets", len(helmets), "rails", len(rails_prefab), "accessory prefabs", len(ACC_INFO) + 2)
