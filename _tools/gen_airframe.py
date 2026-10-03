"""Place the CRYE Airframe into SFHELMETS and write its Workbench resources (python _tools/gen_airframe.py).

After build_airframe.py (FBX in _tools/work/airframe/fbx), export_helmet_colours.py airframe (helmet BCR/NMO, Painter 2048) and
pack_airframe_textures.py (attachment BCR/NMO). Helmet = shell (hit zone) + Airframe-only accessory slots (user: its attachments
are placed for the Airframe and must not fit the SF) + the shared GRS NVG slot. Every texture meta carries MaxSize "2048".
Colour = per-colour xob (OUTLAW convention). Helpers (metas, emats, accessory prefab, GUID store) come from gen_sf.py's
helper section.
"""
import os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
_acc = _src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")]
exec(_acc)

AFX = ROOT + "_tools/work/airframe/fbx/"
EXP = ROOT + "_tools/work/painter/export/"
AF = "ASSETS/AIRFRAME/"
AFA = "ASSETS/Airframe Accessories/"
PF = "Prefabs/Helmets/Airframe/"
PFA = "Prefabs/Airframe Accessories/"


def place_af(part, rel_fbx, materials, utm_gm=None):
    item_fbx = rel_fbx[:-4] + "_Item.fbx"
    os.makedirs(os.path.dirname(ADDON + rel_fbx), exist_ok=True)
    shutil.copyfile(AFX + part + ".fbx", ADDON + rel_fbx)
    shutil.copyfile(AFX + part + "_Item.fbx", ADDON + item_fbx)
    worn, item = rel_fbx[:-4] + ".xob", item_fbx[:-4] + ".xob"
    xob_meta(worn, materials, True, [("UTM_Helmet", "FireGeo", utm_gm)] if utm_gm else [])
    xob_meta(item, materials, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
    return worn, item


def emat_full(rel, bcr, nmo, opacity=None):
    body = f'MatPBRBasic {{\n AllowUserAlphaBias 1\n DisableUserAphaInShadow 1\n BCRMap "{ref(bcr)}"\n'
    if opacity:
        body += f' OpacityMap "{ref(opacity)}"\n'
    body += f' NMOMap "{ref(nmo)}"\n}}\n'
    write(rel, body)
    simple_meta(rel, "EMATResourceClass")


def opacity_meta(rel):
    m = ['MetaFileClass {', f' Name "{ref(rel)}"', ' Configurations {']
    for p in ("PC",) + PLATFORMS:
        m += [f'  PNGResourceClass {p} : "{TEX["BCR"][p]}" {{', '   MaxSize "2048"', '  }']
    m += [' }', '}', '']
    write(rel + ".meta", "\n".join(m))


def tex_emat(d, stem, opacity=False):
    """d = Data folder (rel, ends with /), stem = texture stem; returns the emat ref."""
    bcr, nmo = d + stem + "_BCR.edds", d + stem + "_NMO.edds"
    edds_meta(bcr); edds_meta(nmo)
    op = None
    if opacity:
        op = d + stem + "_Opacity.edds"
        opacity_meta(op)
    emat_full(d + stem + ".emat", bcr, nmo, op)
    return ref(d + stem + ".emat")


# ================================================================ slot types
AREAS = {"EarPro": "GRS_Airframe_EarPro", "Cover": "GRS_Airframe_Cover", "Strobe": "GRS_Airframe_Strobe",
         "Light": "GRS_Airframe_Light", "Rear": "GRS_Airframe_Rear", "Mount": "GRS_Airframe_Mount"}
sc = read("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c")
add = [a for a in AREAS.values() if a not in sc]
if add:
    sc = sc.rstrip() + "\n\n// CRYE Airframe attachment slots (placed for the Airframe only)\n" + "".join(f"class {a}: LoadoutAreaType{{}};\n" for a in add)
    write("Scripts/Game/OUTLAW_Helmet_LoadoutAreas.c", sc)

# ================================================================ helmets
COLOURS = [("AOR1", "AOR1", "AOR1"), ("MC", "MC", "MC"), ("MCB", "MCB", "MCB"), ("ODGreen", "OD", "OD Green"),
           ("RG", "RG", "RG"), ("Tan", "TAN", "Tan")]
helmets = []
for code, tag, pretty in COLOURS:
    folder = f"{AF}AIRFRAME {code}/"
    d = folder + "Data/"
    os.makedirs(ADDON + d, exist_ok=True)
    for kind in ("BCR", "NMO"):
        shutil.copyfile(f"{EXP}AF_{tag}_{kind}.png", f"{ADDON}{d}{code}Airframe_{kind}.png")
    mat = tex_emat(d, f"{code}Airframe")
    worn, item = place_af("AF_Shell", folder + "Airframe.fbx", [("MI_Helmet_CRYE_Airframe_Tan", mat)], GM_BALLISTIC)
    helmets.append((code, pretty, worn, item))

# ================================================================ attachments
# part -> [(variant label, folder, [(source material, texture stem or existing emat ref, opacity)])], slot, pretty name
COUNTERWEIGHT_EMAT = "ASSETS/Helmet Accessories/COUNTERWEIGHT/Data/MI_NVG_Counterweight_OpsCore_Kit_Coyote.emat"
ATT = {
    "AF_ComtacVII": ("EarPro", "Comtac VII (Airframe)", [("Coyote", [("MI_EarPro_Peltor_ComTac_VII_WM_Coyote", "ComtacVII/Data/ComtacVII_Coyote", False)]),
                                                         ("Gray", [("MI_EarPro_Peltor_ComTac_VII_WM_Coyote", "ComtacVII/Data/ComtacVII_Gray", False)])]),
    "AF_Cover": ("Cover", "Airframe Cover", [("OCP", [("MI_Helmet_CRYE_Airframe_Cover_OCP", "Cover/Data/AirframeCover_OCP", True)]),
                                             ("Coyote", [("MI_Helmet_CRYE_Airframe_Cover_OCP", "Cover/Data/AirframeCover_Coyote", True)])]),
    "AF_Helstar": ("Strobe", "Helstar 6 Strobe (Airframe)", [("", [("MI_Helmet_Strobe_CS_HELSTAR_6_G3", "Helstar/Data/Helstar6", True)])]),
    "AF_TNVCLight": ("Light", "TNVC Helmet Light (Airframe)", [("FDE", [("MI_Light_TNVC_FDE", "TNVCLight/Data/TNVCLight_FDE", False)]),
                                                                ("Black", [("MI_Light_TNVC_FDE", "TNVCLight/Data/TNVCLight_Black", False)])]),
    "AF_OpsCoreCounterweight": ("Rear", "Ops-Core Counterweight (Airframe)", [("Coyote", [("MI_NVG_Counterweight_OpsCore_Kit_Coyote", None, False)])]),
    "AF_Mohawk": ("Rear", "TNVC Mohawk + L3Harris Battery (Airframe)", [
        ("OCP", [("MI_NVG_Counterweight_TNVC_Mohawk_MK3_G2_OCP", "Mohawk/Data/Mohawk_OCP", False), ("MI_NVG_L3Harris_BatteryPack_WM", "Mohawk/Data/L3HarrisBattery", False)]),
        ("Coyote", [("MI_NVG_Counterweight_TNVC_Mohawk_MK3_G2_OCP", "Mohawk/Data/Mohawk_Coyote", False), ("MI_NVG_L3Harris_BatteryPack_WM", "Mohawk/Data/L3HarrisBattery", False)])]),
    "AF_G24": ("Mount", "Wilcox G24 Mount (Airframe)", [("Tan", [("MI_NVG_Mount_Wilcox_G24_Tan", "G24/Data/G24_Tan", False)]),
                                                         ("Black", [("MI_NVG_Mount_Wilcox_G24_Tan", "G24/Data/G24_Black", False)])]),
}
acc_prefabs = []
for part, (slot, pretty, variants) in ATT.items():
    short = part[3:]
    for label, mats in variants:
        mat_refs = []
        for src, stem, opacity in mats:
            if stem is None:
                mat_refs.append((src, ref(COUNTERWEIGHT_EMAT)))
            else:
                d, s = AFA + stem.rsplit("/", 1)[0] + "/", stem.rsplit("/", 1)[1]
                mat_refs.append((src, tex_emat(d, s, opacity)))
        folder = f"{AFA}{short}/" + (label + "/" if label else "")
        worn, item = place_af(part, folder + short + ".fbx", mat_refs)
        name = pretty + (f" ({label})" if label else "")
        p = f"{PFA}{short}{('_' + label) if label else ''}.et"
        accessory_prefab(p, name, "Airframe attachment", AREAS[slot], worn, item)
        acc_prefabs.append(p)


# ================================================================ helmet prefabs (standalone, one per colour)
NVG_OFFSET = (0.0016, 0.0337 + 0.0139, -0.1209 + 0.0151)     # SF NVG slot moved by the shroud-front delta of the 0.91-scaled Airframe (15.1 mm back, 13.9 mm up)


def helmet_prefab(rel, name, worn, item):
    k = "c:" + rel + ":"
    c = lambda n: "{%s}" % guid(k + n)
    slots = ""
    for sname, area in AREAS.items():
        slots += f'    LoadoutSlotInfo {sname} {{\n     InheritParentSkeleton 1\n     AreaType {area} "{c("area_" + sname)}" {{\n     }}\n    }}\n'
    slots += (f'    LoadoutSlotInfo NVG {{\n     PivotID "Head"\n     Offset {NVG_OFFSET[0]:.4f} {NVG_OFFSET[1]:.4f} {NVG_OFFSET[2]:.4f}\n'
              f'     Angles 0 -179.996 0\n     AreaType OUTLAW_Helmet_NVG "{c("area_NVG")}" {{\n     }}\n    }}\n')
    t = f'''GameEntity {{
 ID "{guid("id:" + rel)}"
 components {{
  ParametricMaterialInstanceComponent "{c("pmi")}" {{
   UserParamAlpha 0
   ApplyPropertiesWhenMeshChanged 1
  }}
  Persistence "{c("pers")}" {{
  }}
  ClothNodeStorageComponent "{c("store")}" {{
   Attributes SCR_ItemAttributeCollection "{c("sattr")}" {{
    ItemDisplayName UIInfo "{c("sui")}" {{
     Name "{name}"
     Description "Modular CRYE Airframe helmet. Ear pro, cover, strobe, light, rear counterweight/battery, NVG mount and NVG slots."
    }}
    ItemPhysAttributes ItemPhysicalAttributes "{c("sphys")}" {{
     SizeSetupStrategy Manual
     ItemDimensions 25 25 25
    }}
    CustomAttributes {{
     PreviewRenderAttributes "{c("sprev")}" {{
      CameraOrbitAngles -25 30 0
      FOV 65
      ShowAllChildrens 1
     }}
    }}
   }}
   StoragePurpose 0x40 0
  }}
  ColliderHistoryComponent "{c("colh")}" {{
  }}
  InventoryItemComponent "{c("inv")}" {{
   Enabled 0
   Attributes SCR_ItemAttributeCollection "{c("attr")}" {{
    ItemDisplayName UIInfo "{c("ui")}" {{
     Name "{name}"
    }}
    ItemPhysAttributes ItemPhysicalAttributes "{c("phys")}" {{
     Weight 1.3
     SizeSetupStrategy Manual
     ItemDimensions 20 20 20
     ItemVolume 2500
    }}
    CustomAttributes {{
     PreviewRenderAttributes "{c("prev")}" {{
      CameraOrbitAngles -25 25 0
      CameraDistanceToItem 1.5
      FOV 10
      PreviewWornModel 0
     }}
     SCR_HeadgearPhysicsObserverAttribute "{c("obs")}" {{
     }}
    }}
   }}
  }}
  MeshObject "{c("mesh")}" {{
   Object "{ref(item)}"
   InheritVisibility 1
  }}
  RigidBody "{c("rb")}" {{
   Mass 1.3
   LinearDamping 0.2
   AngularDamping 0.4
   SimState None
   ModelGeometry 1
  }}
  SCR_ArmorDamageManagerComponent "{c("dmg")}" {{
   "Additional hit zones" {{
    SCR_ArmorHitZone helmet {{
     ColliderNames {{
      "UTM_Helmet"
     }}
     HZDefault 1
     MaxHealth 10000
     m_eHitZoneGroup HEAD
    }}
   }}
   m_fPassedDamageScale 4
   m_bIsDetachable 1
  }}
  SCR_ItemOutfitFactionComponent "{c("fac")}" {{
   m_OutfitDataHolder SCR_OutfitFactionDataHolder "{c("fach")}" {{
    m_aOutfitFactionData {{
     SCR_OutfitFactionData "{c("facd")}" {{
      m_AffiliatedFactionKey "US"
      m_iOutfitFactionValue 15
     }}
    }}
   }}
  }}
  SCR_SoundDataComponent "{c("snd")}" {{
   m_aAudioSourceConfiguration {{
    SCR_AudioSourceConfiguration "{c("snd1")}" {{
     m_sSoundProject "{{12A94705DF2BFD25}}Sounds/Items/_SharedData/PickUp/Items_PickUp_Generic.acp"
     m_sSoundEventName "SOUND_PICK_UP"
    }}
    SCR_AudioSourceConfiguration "{c("snd2")}" {{
     m_sSoundProject "{{12A94705DF2BFD25}}Sounds/Items/_SharedData/PickUp/Items_PickUp_Generic.acp"
     m_sSoundEventName "SOUND_EQUIP"
     m_eFlags 0
    }}
    SCR_AudioSourceConfiguration "{c("snd3")}" {{
     m_sSoundProject "{{0737072109E39224}}Sounds/Items/_SharedData/Drop/Items_Drop_Helmet.acp"
     m_sSoundEventName "SOUND_DROP"
    }}
   }}
  }}
  BaseLoadoutClothComponent "{c("cloth")}" {{
   AreaType LoadoutHeadCoverArea "{c("area")}" {{
   }}
   Slots {{
{slots}   }}
   WornModel "{ref(worn)}"
   ItemModel "{ref(item)}"
   PhysicsOnWearEnabled 1
   AnimateCollidersOnWear 1
   SoundInt 110
  }}
  ActionsManagerComponent "{c("am")}" {{
   ActionContexts {{
    UserActionContext "{c("ctx")}" {{
     ContextName "default"
     Position PointInfo "{c("ctxp")}" {{
      Offset 0 0.1 0
     }}
    }}
   }}
   additionalActions {{
    SCR_EquipClothAction "{c("equip")}" {{
     ParentContextList {{
      "default"
     }}
     UIInfo SCR_ActionUIInfo "{c("equipui")}" {{
      Name "#AR-Inventory_Equip"
      m_sIconName "pick-up"
     }}
     "Sort Priority" -10
    }}
    SCR_PickUpItemAction "{c("pick")}" {{
     ParentContextList {{
      "default"
     }}
     UIInfo SCR_ActionUIInfo "{c("pickui")}" {{
      Name "#AR-Inventory_PickUp"
      m_sIconName "pick-up"
     }}
    }}
   }}
  }}
  NwkPhysicsMovementComponent "{c("nwk")}" {{
  }}
  RplComponent "{c("rpl")}" {{
   "Rpl State Override" Runtime
   "Parent Node From Parent Entity" 0
  }}
  Hierarchy "{c("hier")}" {{
  }}
 }}
}}
'''
    write(rel, t)
    if not os.path.exists(ADDON + rel + ".meta"):
        simple_meta(rel, "EntityTemplateResourceClass")


helmet_prefabs = []
for code, pretty, worn, item in helmets:
    p = f"{PF}Airframe_Helmet_{code}.et"
    helmet_prefab(p, f"CRYE Airframe ({pretty})", worn, item)
    helmet_prefabs.append(p)

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
    return text[:j] + "".join(cat_entry(p, kind) for p in prefabs if "{%s}" % rguid(p) not in text) + text[j:]


cat = add_to_list(cat, "Outlaw Helmets", helmet_prefabs, "HEADWEAR")
cat = add_to_list(cat, "Outlaw Helmet Accesories", acc_prefabs, "EQUIPMENT")
write(CAT, cat)
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
print("airframe helmets", len(helmet_prefabs), "attachment prefabs", len(acc_prefabs))
