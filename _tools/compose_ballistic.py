"""Write the Painter-textured Ballistic islands into a colour's SF_BCR / SF_NMO (python _tools/compose_ballistic.py MCB ...).

Painter project: _tools/work/painter/SF_Ballistic_texturing.spp (the user's MCB HELMET.spp stack on Bump + Rails +
Ballistic, Ballistic shell/velcro added to the Plastic Grainy Soft / Bebra_Velcro masks). Its 4K export lands in
_tools/work/painter/export/<TAG>_BCR.png / <TAG>_NMO.png (NMO = DirectX normal RG + metallic B, the user's packing).
Only texels of the Ballistic's own UV islands (+4 px bleed into unused atlas) are written, on top of the ORIGINAL
textures in _tools/work/tex_backup; every texel the Bump or rails use stays byte-identical (asserted).
"""
import sys
import numpy as np
from PIL import Image

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
A = ROOT + "SFHELMETS/ASSETS/"
WORK = ROOT + "_tools/work/"
SETS = {"AOR1": ("HELMET AOR1", "AOR1SF_BCR.tif", "AOR1SF_NMO.tif"), "MCB": ("HELMET BLACK", "mcbSF_BCR.tif", "mcbSF_NMO.tif"),
        "OD": ("HELMET GREEN", "grSF_BCR.tif", "grSF_NMO.tif"), "MC": ("HELMET MC", "SF_BCR.tif", "SF_NMO.tif"),
        "RG": ("HELMET RG", "RGSF_BCR.tif", "RGSF_NMO.tif"), "TAN": ("HELMET TAN", "tanSF_BCR.tif", "tanSF_NMO.tif")}

m = np.load(WORK + "ballistic_map.npz")
x, y, used = m["x"], m["y"], m["used"]
RES = used.shape[0]
target = np.zeros((RES, RES), bool); target[y, x] = True
free = ~used


def bleed(img, filled, n=4):
    img = img.astype(np.float32)
    for _ in range(n):
        acc = np.zeros_like(img); cnt = np.zeros(filled.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            sf = np.roll(filled, (dy, dx), (0, 1)); si = np.roll(img, (dy, dx), (0, 1))
            acc += si * sf[..., None]; cnt += sf
        grow = free & ~filled & (cnt > 0)
        img[grow] = acc[grow] / cnt[grow][:, None]
        filled = filled | grow
    return img


for tag in sys.argv[1:]:
    folder, bcr_n, nmo_n = SETS[tag]
    for kind, name in (("BCR", bcr_n), ("NMO", nmo_n)):
        src = np.asarray(Image.open(f"{WORK}tex_backup/{folder}_{name}").convert("RGB")).astype(np.float32)
        pt = Image.open(f"{WORK}painter/export/{tag}_{kind}.png").convert("RGB").resize((RES, RES), Image.LANCZOS)
        pt = np.asarray(pt).astype(np.float32)
        out = src.copy()
        out[target] = pt[target]
        out = bleed(out, target.copy())
        assert np.array_equal(out[used].round(), src[used]), tag + " " + kind + ": a Bump texel changed"
        Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8), "RGB").save(f"{A}{folder}/Data/{name}", compression="tiff_lzw")
    print(tag, "written:", folder, bcr_n, nmo_n)
