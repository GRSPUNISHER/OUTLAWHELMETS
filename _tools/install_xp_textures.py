"""Install the XP Painter exports into SFHELMETS (python _tools/install_xp_textures.py, after export_helmet_colours.py xp / xp4).

- XP1 / Carbon1 / XP4M (loop panels on Bebra_Velcro, user 2026-09-30) are copied over each colour's existing PNGs; metas kept.
- XP1H4 = XP1 baked on the 4-hole shells (no 3-hole shroud-frame AO, user: "still has the shadow on the xp 4-hole"): new
  {code}XP_XP1H4_BCR/NMO.png + XP_XP1H4.emat per colour, and the XP4 / XPC4 worn + item xob metas assign it to source
  material "XP1" (text edit of the current meta, nothing else in it changes). XP3 / XPC3 / rails keep XP_XP1.emat.
Copies straight from Painter's 2048 export, no resizing.
"""
import os, re, shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
_src = open(ROOT + "_tools/gen_sf.py", encoding="utf-8").read()
exec(_src[:_src.index("# ================================================================ helmets")])

EXP = ROOT + "_tools/work/painter/export/"
COLOURS = [("AOR1", "AOR1"), ("MC", "MC"), ("MCB", "MCB"), ("ODGreen", "OD"), ("RG", "RG"), ("Tan", "TAN")]
changed = []
for code, tag in COLOURS:
    d = f"ASSETS/XP/XP {code}/Data/"
    for tset in ("XP1", "Carbon1", "XP4M"):
        for kind in ("BCR", "NMO"):
            shutil.copyfile(f"{EXP}{tset}_{tag}_{kind}.png", f"{ADDON}{d}{code}XP_{tset}_{kind}.png")
            changed.append(f"{d}{code}XP_{tset}_{kind}.png")
    stem = f"{code}XP_XP1H4"
    for kind in ("BCR", "NMO"):
        shutil.copyfile(f"{EXP}XP1H4_{tag}_{kind}.png", f"{ADDON}{d}{stem}_{kind}.png")
        changed.append(f"{d}{stem}_{kind}.png")
        if not os.path.exists(f"{ADDON}{d}{stem}_{kind}.edds.meta"):
            edds_meta(f"{d}{stem}_{kind}.edds")
    if not os.path.exists(ADDON + d + "XP_XP1H4.emat"):
        emat(d + "XP_XP1H4.emat", d + stem + "_BCR.edds", d + stem + "_NMO.edds")
    em = ref(d + "XP_XP1H4.emat")
    for key in ("XP4", "XPC4"):
        for suffix in ("", "_Item"):
            m = f"ASSETS/XP/XP {code}/{key}{suffix}.xob.meta"
            t = read(m)
            t2, n = re.subn(r'(SourceMaterial "XP1"\s*AssignedMaterial ")[^"]+(")', lambda x: x.group(1) + em + x.group(2), t)
            if n != 1:
                raise SystemExit(f"{m}: expected one XP1 assign, found {n}")
            if t2 != t:
                write(m, t2)
            print(code, key + suffix, "XP1 ->", em)
json.dump(_G, open(_GF, "w"), indent=0, sort_keys=True)
open(ROOT + "_tools/work/xp/installed_textures.txt", "w").write("\n".join(changed))
print("textures", len(changed))
