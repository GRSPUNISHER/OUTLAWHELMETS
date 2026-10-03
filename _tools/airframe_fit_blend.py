"""Make an editable Airframe fit .blend: the Reforger body + armature from the SF .blend, plus every Airframe part at its current
export placement (build_airframe.py transform), as plain objects. Saved to _tools/work/airframe/Airframe_fit.blend.

  blender -b "<Fast SF v2 BUMP AND BALLISTIC HELMET.blend>" --python _tools/airframe_fit_blend.py
"""
import bpy, os, json
from mathutils import Matrix

TOOLS = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(TOOLS, "work", "airframe", "raw")
OUT = os.path.join(TOOLS, "work", "airframe", "Airframe_fit.blend")
PARTS = ["AF_Shell", "AF_Cover", "AF_ComtacVII", "AF_Helstar", "AF_TNVCLight", "AF_OpsCoreCounterweight", "AF_Mohawk", "AF_G24"]
M = Matrix(json.load(open(os.path.join(TOOLS, "work", "airframe", "fit_airframe_scale.json")))["M"])

keep = {"Body_LOD0", "Armature"}
for o in list(bpy.data.objects):
    if o.name not in keep and not (o.parent and o.parent.name == "Armature" and o.type == 'EMPTY'):
        bpy.data.objects.remove(o, do_unlink=True)
col = bpy.data.collections.new("AIRFRAME")
bpy.context.scene.collection.children.link(col)
for part in PARTS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(RAW, part + ".fbx"))
    for o in [x for x in bpy.data.objects if x not in before]:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.data.transform(M @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.name = part
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
