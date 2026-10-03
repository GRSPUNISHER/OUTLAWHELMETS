"""Copy the Maritime Painter exports over each colour's existing PNGs (python _tools/install_maritime_textures.py, after
export_helmet_colours.py maritime). Texture-only refresh (user 2026-09-30: rail shadows removed by the "Only same mesh name"
AO rebake); metas / emats / models untouched, straight 2048 copies from Painter.
"""
import shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
ADDON = ROOT + "SFHELMETS/"
EXP = ROOT + "_tools/work/painter/export/"
COLOURS = [("AOR1", "AOR1"), ("MC", "MC"), ("MCB", "MCB"), ("ODGreen", "OD"), ("RG", "RG"), ("Tan", "TAN")]
n = 0
for code, tag in COLOURS:
    d = f"{ADDON}ASSETS/MARITIME/MARITIME {code}/Data/"
    for tset in ("MT", "KitA"):
        for kind in ("BCR", "NMO"):
            shutil.copyfile(f"{EXP}{tset}_{tag}_{kind}.png", f"{d}{code}Maritime{tset}_{kind}.png")
            n += 1
print("maritime textures", n)
