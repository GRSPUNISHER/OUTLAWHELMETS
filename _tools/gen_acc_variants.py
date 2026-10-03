"""Colour variants of the AMP, PVS-31 BRS, Ops-Core counterweight and Comtac VII in SFHELMETS, for every fit
(python _tools/gen_acc_variants.py assets   then, once Workbench has imported the models,   ... prefabs).

User 2026-09-30: "i need variants of the counter weights, AMPs, BRS, Comtacs". Textures from acc_variant_textures.py:
AMP Black / RG, BRS Coyote / OD, counterweight MC / RG / Black, Comtac VII Grey / Green. Each colour is its own folder with
per-colour xob copies of every fit the original has (standard / SF, the user's Maritime fit, the user's XP fit) and its own
emat (per-colour xobs: prefab material overrides did not take on attachments). The Maritime Comtac VII is a prefab-only copy
on the standard model, like the existing ones; the Maritime uses the standard counterweight (shared slot).
Stage "assets" writes metas / emats / textures first and copies the FBX last (a prefab that references a not-yet-imported
xob made Workbench drop the collider params from its meta); stage "prefabs" writes the prefabs and catalog entries.
"""
import os, re, shutil, sys

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])
exec(_src[_src.index("# ================================================================ accessory prefabs"):_src.index("ACC_INFO = {")])

TEXDIR = ROOT + "_tools/work/acc_variants/tex/"
ACC = "ASSETS/Helmet Accessories/"
STAGE = sys.argv[1] if len(sys.argv) > 1 else "assets"

# item -> dict(orig dir, colours {name: (folder, texture stem, nmo source or None)}, fits [(fit, src fbx, prefab stem, area, own model)])
ITEMS = {
    "AMP": dict(src_xob=ACC + "AMP/OpsCore_AMP.xob", desc="Ear Pro", label="Ops-Core AMP",
                colours={"Black": (ACC + "AMP/BLACK AMP/", "OpsCore_AMP_Black", ACC + "AMP/Data/OpsCore_AMP_NMO.png"),
                         "RG": (ACC + "AMP/RG AMP/", "OpsCore_AMP_RG", ACC + "AMP/Data/OpsCore_AMP_NMO.png")},
                fits=[("", ACC + "AMP/OpsCore_AMP.fbx", "Prefabs/EarPro/OpsCore AMP ({c})", "OUTLAW_Helmet_EarPro", True),
                      ("Maritime", ACC + "AMP/Maritime/OpsCore_AMP_Maritime.fbx", "Prefabs/EarPro/OpsCore AMP ({c}) (Maritime)", "OUTLAW_Helmet_MaritimeEarPro", True),
                      ("XP", ACC + "AMP/XP/OpsCore_AMP_XP.fbx", "Prefabs/EarPro/OpsCore AMP ({c}) (XP)", "OUTLAW_Helmet_XPEarPro", True)]),
    "BRS": dict(src_xob=ACC + "BATTERYPACK/batterypack.xob", desc="Helmet Attachment", label="PVS-31 BRS",
                colours={"Coyote": (ACC + "BATTERYPACK/COYOTE BRS/", "PVS31_BRS_Coyote", None),
                         "OD": (ACC + "BATTERYPACK/OD BRS/", "PVS31_BRS_OD", None)},
                fits=[("", ACC + "BATTERYPACK/batterypack.fbx", "Prefabs/Batteries/PVS-31 BRS ({c})", "OUTLAW_Helmet_BRS", True),
                      ("Maritime", ACC + "BATTERYPACK/Maritime/batterypack_Maritime.fbx", "Prefabs/Batteries/PVS-31 BRS ({c}) (Maritime)", "OUTLAW_Helmet_MaritimeBRS", True),
                      ("XP", ACC + "BATTERYPACK/XP/batterypack_XP.fbx", "Prefabs/Batteries/PVS-31 BRS ({c}) (XP)", "OUTLAW_Helmet_XPBRS", True)]),
    "Counterweight": dict(src_xob=ACC + "COUNTERWEIGHT/counterweight.xob", desc="Helmet Attachment", label="Ops-Core Counterweight",
                          colours={c: (ACC + f"COUNTERWEIGHT/{c.upper()} COUNTERWEIGHT/", f"OpsCoreCounterweight_{c}",
                                       ACC + "COUNTERWEIGHT/Data/OpsCoreCounterweight_Coyote_NMO.png") for c in ("MC", "RG", "Black")},
                          fits=[("", ACC + "COUNTERWEIGHT/counterweight.fbx", "Prefabs/Batteries/OpsCore Counterweight ({c})", "OUTLAW_Helmet_Counterweight", True),
                                ("XP", ACC + "COUNTERWEIGHT/XP/counterweight_XP.fbx", "Prefabs/Batteries/OpsCore Counterweight ({c}) (XP)", "OUTLAW_Helmet_XPCounterweight", True)]),
    "Comtac VII": dict(src_xob=ACC + "COMTACS/RG COMTACS/comtacviinostrap.xob", desc="Ear Pro", label="Comtac VII",
                       colours={c: (ACC + f"COMTACS/{c.upper()} COMTACS/", f"PeltorComtac_VII_{c}", None) for c in ("Grey", "Green")},
                       fits=[("", ACC + "COMTACS/RG COMTACS/comtacviinostrap.fbx", "Prefabs/EarPro/Comtacs ({c})", "OUTLAW_Helmet_EarPro", True),
                             ("Maritime", ACC + "COMTACS/RG COMTACS/comtacviinostrap.fbx", "Prefabs/EarPro/Comtacs ({c}) (Maritime)", "OUTLAW_Helmet_MaritimeEarPro", False),
                             ("XP", ACC + "COMTACS/RG COMTACS/XP/comtacviinostrap_XP.fbx", "Prefabs/EarPro/Comtacs ({c}) (XP)", "OUTLAW_Helmet_XPEarPro", True)]),
}


def dst_fbx(folder, fit, src):
    return folder + (fit + "/" if fit else "") + os.path.basename(src)


copies, prefabs = [], []
for key, it in ITEMS.items():
    srcmats = [s for s, _ in existing_assigns(it["src_xob"])]
    for col, (folder, stem, nmo_src) in it["colours"].items():
        d = folder + "Data/"
        os.makedirs(ADDON + d, exist_ok=True)
        bcr, nmo = d + stem + "_BCR.edds", d + stem + "_NMO.edds"
        em = d + srcmats[0] + ".emat"
        if STAGE == "assets":
            edds_meta(bcr); edds_meta(nmo)
            emat(em, bcr, nmo)
            copies += [(TEXDIR + stem + "_BCR.png", ADDON + d + stem + "_BCR.png"),
                       ((ADDON + nmo_src) if nmo_src else (TEXDIR + stem + "_NMO.png"), ADDON + d + stem + "_NMO.png")]
        mats = [(srcmats[0], ref(em))]
        std = None
        for fit, src, pstem, area, own in it["fits"]:
            if own:
                worn = dst_fbx(folder, fit, src)[:-4] + ".xob"
                item = worn[:-4] + "_Item.xob"
                if not fit:
                    std = (worn, item)
                if STAGE == "assets":
                    os.makedirs(os.path.dirname(ADDON + worn), exist_ok=True)
                    xob_meta(worn, mats, True)
                    xob_meta(item, mats, False, [("UCX_Item", "ItemFireView", GM_ITEM)])
                    copies += [(ADDON + src, ADDON + worn[:-4] + ".fbx"), (ADDON + src[:-4] + "_Item.fbx", ADDON + item[:-4] + ".fbx")]
            else:
                worn, item = std
            p = pstem.format(c=col) + ".et"
            if STAGE == "prefabs":
                name = f"{it['label']} ({col})" + (f" ({fit})" if fit else "")
                accessory_prefab(p, name, it["desc"], area, worn, item)
            prefabs.append(p)

if STAGE == "assets":
    for s, d in copies:
        shutil.copyfile(s, d)
    print("assets: files copied", len(copies))
else:
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
    print("prefabs", len(prefabs))
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
