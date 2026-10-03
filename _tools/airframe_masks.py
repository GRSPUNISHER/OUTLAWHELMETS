"""Layer masks for the MCB HELMET.spp stack on the CRYE Airframe, from the vendor ID map (python _tools/airframe_masks.py).

Each ID colour is assigned to the stack layer that covers the same kind of part on the SF (shell paint, hardware plastic,
webbing, velcro loop, buckles, pads). Nearest-palette classification (the ID map is anti-aliased), 4 px dilation.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
ID = "C:/Users/lebea/OneDrive/Desktop/Cars/Helmet_CRYE_Airframe_v03/Helmet_CRYE_Airframe_v03/Textures/Masks/Helmet_CRYE_Airframe_Mask_ID.png"
OUT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/_tools/work/airframe/painter/masks/"
PALETTE = {(0, 0, 0): None, (49, 81, 135): "shell", (55, 148, 47): "composite", (15, 38, 11): "nylon", (45, 58, 39): "nylon",
           (27, 64, 68): "nylon", (204, 204, 204): "velcro", (26, 65, 204): None, (155, 124, 81): "grain", (61, 61, 61): "rubber",
           (10, 10, 10): "rubber", (169, 44, 204): None, (135, 107, 81): "grain", (38, 73, 101): None}
im = Image.open(ID).convert("RGB")
if im.size != (4096, 4096):
    im = im.resize((4096, 4096), Image.NEAREST)
a = np.asarray(im).astype(np.int32)
cols = np.array(list(PALETTE.keys()))
d = ((a[:, :, None, :] - cols[None, None]) ** 2).sum(-1) if False else None
best = np.zeros(a.shape[:2], np.int32); bestd = np.full(a.shape[:2], 1 << 30)
for i, c in enumerate(cols):
    di = ((a - c) ** 2).sum(-1)
    m = di < bestd
    best[m] = i; bestd[m] = di[m]
labels = np.array([PALETTE[tuple(c)] for c in cols], dtype=object)
for cls in ("shell", "composite", "nylon", "velcro", "grain", "rubber"):
    mask = np.isin(best, [i for i, l in enumerate(labels) if l == cls])
    mask = ndimage.binary_dilation(mask, iterations=4)
    Image.fromarray((mask * 255).astype(np.uint8), "L").save(OUT + f"af_{cls}.png")
    print(cls, round(mask.mean() * 100, 2), "%")
