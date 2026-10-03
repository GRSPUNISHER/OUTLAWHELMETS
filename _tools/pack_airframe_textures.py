"""Pack the CRYE Airframe attachments' vendor PBR maps into Enfusion BCR / NMO PNGs (python _tools/pack_airframe_textures.py).

  BCR: RGB base colour, A roughness      NMO: RG DirectX normal (the pack ships *_DirectX_Normal), B metalness, A AO
Vendor colour options become separate textures (same normal/rough/metal/AO). Opacity maps are copied as *_Opacity.png.
The OpsCore counterweight reuses the textures already packed for the SF (same vendor texture set).
"""
import os, shutil
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
T = "C:/Users/lebea/OneDrive/Desktop/Cars/Helmet_CRYE_Airframe_v03/Helmet_CRYE_Airframe_v03/Textures/"
OUT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/SFHELMETS/ASSETS/Airframe Accessories/"
RES = 2048

C7 = T + "PBR_EarPro_Peltor_ComTac_VII_tx/EarPro_Peltor_ComTac_VII_"
CV = T + "PBR_Helmet_CRYE_Airframe_Cover_tx/Helmet_CRYE_Airframe_Cover_"
HS = T + "PBR_NVG_Strobe_CS_HELSTAR_6_G3_tx/NVG_Strobe_CS_HELSTAR_6_G3_"
LT = T + "PBR_Light_TNVC_tx/"
MH = T + "PBR_NVG_Counterweight_TNVC_Mohawk_MK3_G2_tx/NVG_Counterweight_TNVC_Mohawk_MK3_G2_"
LB = T + "PBR_NVG_L3Harris_BatteryPack_WM_tx/NVG_L3Harris_BatteryPack_WM_"
G24 = T + "PBR_NVG_Mount_Wilcox_G24_tx/NVG_Mount_Wilcox_G24_"

# out stem -> (base colour, roughness, metalness, AO, DirectX normal, opacity or None)
SETS = {
    "ComtacVII/Data/ComtacVII_Coyote": (C7 + "Coyote_BaseColor.png", C7 + "Coyote_Roughness.png", C7 + "Coyote_Metalness.png", C7 + "Coyote_AO.png", C7 + "Coyote_DirectX_Normal.png", None),
    "ComtacVII/Data/ComtacVII_Gray": (C7 + "Gray_BaseColor.png", C7 + "Coyote_Roughness.png", C7 + "Coyote_Metalness.png", C7 + "Coyote_AO.png", C7 + "Coyote_DirectX_Normal.png", None),
    "Cover/Data/AirframeCover_OCP": (CV + "OCP_BaseColor.png", CV + "OCP_Roughness.png", CV + "OCP_Metalness.png", CV + "OCP_AO.png", CV + "OCP_DirectX_Normal.png", CV + "OCP_Opacity.png"),
    "Cover/Data/AirframeCover_Coyote": (CV + "Coyote_BaseColor.png", CV + "OCP_Roughness.png", CV + "OCP_Metalness.png", CV + "OCP_AO.png", CV + "OCP_DirectX_Normal.png", CV + "OCP_Opacity.png"),
    "Helstar/Data/Helstar6": (HS + "BaseColor.png", HS + "Roughness.png", HS + "Metalness.png", HS + "AO.png", HS + "DirectX_Normal.png", HS + "Opacity.png"),
    "TNVCLight/Data/TNVCLight_FDE": (LT + "Helmet_Light_TNVC_BaseColor.png", LT + "Helmet_Light_Roughness.png", LT + "Helmet_Light_TNVC_Metalness.png", LT + "Helmet_Light_TNVC_AO.png", LT + "Helmet_Light_TNVC_Normal_DirectX.png", None),
    "TNVCLight/Data/TNVCLight_Black": (LT + "Helmet_Light_Black_BaseColor.png", LT + "Helmet_Light_Roughness.png", LT + "Helmet_Light_Black_Metalness.png", LT + "Helmet_Light_TNVC_AO.png", LT + "Helmet_Light_TNVC_Normal_DirectX.png", None),
    "Mohawk/Data/Mohawk_OCP": (MH + "OCP_BaseColor.png", MH + "OPC_Roughness.png", MH + "OPC_Metalness.png", MH + "OPC_AO.png", MH + "OPC_DirectX_Normal.png", None),
    "Mohawk/Data/Mohawk_Coyote": (MH + "Coyote_BaseColor.png", MH + "OPC_Roughness.png", MH + "OPC_Metalness.png", MH + "OPC_AO.png", MH + "OPC_DirectX_Normal.png", None),
    "Mohawk/Data/L3HarrisBattery": (LB + "BaseColor.png", LB + "Roughness.png", LB + "Metalness.png", LB + "AO.png", LB + "DirectX_Normal.png", None),
    "G24/Data/G24_Tan": (G24 + "Tan_BaseColor.png", G24 + "Tan_Roughness.png", G24 + "Tan_Metalness.png", G24 + "Tan_AO.png", G24 + "Tan_DirectX_Normal.png", None),
    "G24/Data/G24_Black": (G24 + "BLK_BaseColor.png", G24 + "Tan_Roughness.png", G24 + "Tan_Metalness.png", G24 + "Tan_AO.png", G24 + "Tan_DirectX_Normal.png", None),
}


def load(path, mode):
    im = Image.open(path)
    im = im.convert("RGB").convert("L") if mode == "L" else im.convert(mode)
    if im.size != (RES, RES):
        im = im.resize((RES, RES), Image.LANCZOS)
    return np.asarray(im)


for stem, (bc, rg, mt, ao, nm, op) in SETS.items():
    os.makedirs(os.path.dirname(OUT + stem), exist_ok=True)
    base, rough, metal, occ, n = load(bc, "RGB"), load(rg, "L"), load(mt, "L"), load(ao, "L"), load(nm, "RGB")
    Image.fromarray(np.dstack([base, rough]).astype(np.uint8), "RGBA").save(OUT + stem + "_BCR.png")
    Image.fromarray(np.dstack([n[..., 0], n[..., 1], metal, occ]).astype(np.uint8), "RGBA").save(OUT + stem + "_NMO.png")
    if op:
        Image.fromarray(load(op, "L")).save(OUT + stem + "_Opacity.png")
    print(stem, "base", base.reshape(-1, 3).mean(0).round(0), "opacity" if op else "")
