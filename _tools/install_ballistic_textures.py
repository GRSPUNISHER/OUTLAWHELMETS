"""Copy the Painter-exported Ballistic BCR/NMO (user's MCB stack, per colourway) into each colour folder as the Ballistic's
OWN textures (the Bump's SF_*_BCR/NMO are never touched). Copied exactly as Painter exported them (project 4096, Painter export 2048 - user rule; never resized here).

  python _tools/install_ballistic_textures.py        (then python _tools/gen_sf.py for metas/emats)
"""
import shutil

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
EXP = ROOT + "_tools/work/painter/export/"
# tag -> (colour folder, file prefix)
BALLISTIC_TEX = {"AOR1": ("HELMET AOR1", "AOR1SF"), "MCB": ("HELMET BLACK", "mcbSF"), "OD": ("HELMET GREEN", "grSF"),
                 "MC": ("HELMET MC", "SF"), "RG": ("HELMET RG", "RGSF"), "TAN": ("HELMET TAN", "tanSF")}

if __name__ == "__main__":
    for tag, (folder, prefix) in BALLISTIC_TEX.items():
        for kind in ("BCR", "NMO"):
            shutil.copyfile(f"{EXP}{tag}_{kind}.png", f"{ROOT}SFHELMETS/ASSETS/{folder}/Data/{prefix}Ballistic_{kind}.png")
        print(tag, "->", folder, prefix + "Ballistic_BCR/NMO.png")
