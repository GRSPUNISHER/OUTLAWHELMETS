"""FAST XP / XP Carbon (3-hole, 4-hole) with every attachment, textured, for a look in Blender (Blender 4.5 headless, then
open the .blend):

  blender -b --python _tools/preview_xp.py  [-- <colour code, default AOR1>]

Same build as preview_maritime.py (its helpers are reused). The four shells sit in the Helmet collection in the same place:
XP3 is shown, XP4 / XPC3 / XPC4 are hidden. Saves _tools/work/xp/XP_all_attachments_<code>.blend plus an untouched
..._orig.blend to diff the user's fit against.
"""
import os, shutil, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
_s = open(os.path.join(TOOLS, "preview_maritime.py"), encoding="utf-8").read()
exec(_s[_s.index("import bpy"):_s.index("SLOTS = [")])
XP = f"ASSETS/XP/XP {CODE}/"
SLOTS = [
    ("Helmet", [("XP3 shell", XP + "XP3.fbx"), ("XP4 shell", XP + "XP4.fbx"), ("XPC3 shell", XP + "XPC3.fbx"),
                ("XPC4 shell", XP + "XPC4.fbx")]),
    ("Rails", [("XP rails", XP + "XPRails.fbx")]),
    ("BRS", [("PVS-31 BRS", ACC + "BATTERYPACK/batterypack.fbx")]),
    ("Battery", [("BNVD Battery Pack", ACC + "BNVD BATTERY/bnvdbattery.fbx"),
                 ("ShawBrain Pouch (MC)", ACC + "ShawBrainPouch/MC SHAWBRAIN/shawbrainpouch.fbx")]),
    ("Counterweight", [("Ops-Core Counterweight", ACC + "COUNTERWEIGHT/counterweight.fbx")]),
    ("Earpro", [("Comtac VII (RG)", ACC + "COMTACS/RG COMTACS/comtacviinostrap.fbx"),
                ("Ops-Core AMP", ACC + "AMP/OpsCore_AMP.fbx"),
                ("Comtac VI", ACC + "COMTACS/COMTAC VI/comtacvi.fbx")]),
    ("Scrims", [("HighCut Oak Scrim (MC)", ACC + "Scrims/HighCut Oak MC/HighCut Scrim Oak.fbx"),
                ("HighCut SemiCircle Scrim (MC)", ACC + "Scrims/HighCut Semi MC/HighCut Scrim Oak.fbx")]),
]
exec(_s[_s.index("def res_path(r):"):_s.index("out = os.path.join(")])

out = os.path.join(TOOLS, "work", "xp", f"XP_all_attachments_{CODE}.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
shutil.copyfile(out, out[:-6] + "_orig.blend")
print("SAVED", out)
print("MISSING TEXTURES", missing)
for c in scene.collection.children:
    print(c.name, [(o.name, "hidden" if o.hide_get() else "shown") for o in c.objects])
