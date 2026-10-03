"""Texture the CRYE Airframe in each colourway with the user's MCB HELMET.spp stack (Painter bridge 127.0.0.1:60043).

  python _tools/airframe_colours.py AOR1 MC OD RG TAN

Painter project: _tools/work/airframe/painter/AF_texturing.spp (the user's stack, transferred as a smart material, masks
rebuilt from the Airframe ID map by airframe_masks.py). Colour inputs are the SF Ballistic's final tuned swatches / graded camo
(calibrate_ballistic.py), so an Airframe matches the SF helmets of the same colour. The SF AOR1 shell is the vendor AOR1 atlas,
which the Airframe does not have: its AOR1 shell is the tiling Camo_US_NWU_Type_2_AOR1.png, graded until the shell matches
the AOR1 SF Bump shell. MCB is the stack exactly as the user made it (exported before this script, tag AF_MCB).
Exports _tools/work/painter/export/AF_<TAG>_BCR.png / _NMO.png at 4096.
"""
import glob, json, os, re, socket, sys
import numpy as np
from PIL import Image

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
PW = ROOT + "_tools/work/painter/"
SW = PW + "swatches/"
AFT = "C:/Users/lebea/OneDrive/Desktop/Cars/Helmet_CRYE_Airframe_v03/Helmet_CRYE_Airframe_v03/Textures/PBR_Helmet_CRYE_Airframe_tx/"
BASE = {"AOR1": AFT + "Helmet_CRYE_Airframe_Tan_BaseColor.png", "MC": AFT + "Helmet_CRYE_Airframe_OCP_BaseColor.png",
        "OD": AFT + "Helmet_CRYE_Airframe_Tan_BaseColor.png", "RG": AFT + "Helmet_CRYE_Airframe_Tan_BaseColor.png",
        "TAN": AFT + "Helmet_CRYE_Airframe_Tan_BaseColor.png"}
AOR1_CAMO = "C:/Users/lebea/Downloads/camopk/Camo_US_NWU_Type_2_AOR1.png"
AOR1_SHELL_TARGET = np.array([85.0, 78.3, 70.1])
KEYS = ("velcro", "nylon", "composite", "grain", "rubber")
SHELL = np.asarray(Image.open(PW.replace("painter/", "airframe/painter/masks/") + "af_shell.png").resize((1024, 1024))) > 250


def painter(code):
    s = socket.create_connection(("127.0.0.1", 60043), timeout=900)
    s.sendall((json.dumps({"id": 1, "op": "python.exec", "params": {"code": code}}) + "\n").encode())
    buf = b""
    while b"\n" not in buf:
        buf += s.recv(1 << 20)
    r = json.loads(buf.split(b"\n")[0])
    if not r.get("ok"):
        raise RuntimeError(r)
    return r["result"]


def last(tag, key):
    files = glob.glob(f"{SW}{tag}[0-9]_{key}.png")
    return max(files, key=lambda f: int(re.search(rf"{tag}(\d)_", os.path.basename(f)).group(1)))


def to_lin(c):
    c = np.asarray(c, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def run(cfg, tag, size):
    return painter("import builtins\nPB = builtins.PB\nPB['apply'](" + repr(cfg) + ")\nresult = PB['export']('" + tag + "', " + str(size) + ", " + str(size == 12) + ")")


for tag in sys.argv[1:]:
    sw = {k: last(tag, k) for k in KEYS}
    if tag == "MC":
        shell = ["bitmap", last("MC", "camo"), False]
    elif tag == "AOR1":
        shell = None
    else:
        shell = ["swatch", last(tag, "shell")]
    if shell is None:
        src = np.asarray(Image.open(AOR1_CAMO).convert("RGB")).astype(np.float32)
        gain = np.ones(3)
        for it in range(5):
            graded = f"{SW}AF_AOR1{it}_camo.png"
            Image.fromarray(to_srgb(to_lin(src) * gain).round().astype(np.uint8), "RGB").save(graded)
            run({"base": BASE[tag], "shell": ["bitmap", graded, False], "swatches": sw}, "cal_AF_AOR1", 10)
            got = np.asarray(Image.open(PW + "export/cal_AF_AOR1_BCR.png").convert("RGB").resize((1024, 1024))).astype(float)[SHELL].mean(0)
            print("AOR1 iter", it, "shell", got.round(1), "target", AOR1_SHELL_TARGET)
            if np.abs(got - AOR1_SHELL_TARGET).mean() < 2.0:
                break
            gain = gain * np.clip(to_lin(AOR1_SHELL_TARGET) / (to_lin(got) + 1e-4), 0.2, 5.0)
        shell = ["bitmap", graded, False]
    print(tag, "final export", run({"base": BASE[tag], "shell": shell, "swatches": sw}, "AF_" + tag, 12))
