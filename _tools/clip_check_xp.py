"""Every-vertex clip check of the SF attachments on the XP helmets (Blender 4.5 headless:  blender -b --python _tools/clip_check_xp.py).

For each attachment (worn FBX, placed by the user on the SF) and each helmet (SF baseline, XP3/XP4/XPC3/XPC4): count vertices
that are INSIDE the outer shell (ray from the head centre through the vertex hits the shell beyond it by > 1.5 mm) or INSIDE a
rail (nearest rail point within 2 cm and the vertex is > 1.5 mm behind that rail face). The SF numbers are the baseline the user
accepted; an attachment clips on an XP helmet when it has clearly more penetrating vertices / depth than on the SF.
Writes _tools/work/xp/clip_report.json.
"""
import bpy, bmesh, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOOLS = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(TOOLS, "work")
OUTLAW = os.path.join(TOOLS, "..", "SFHELMETS", "ASSETS")
C = Vector((0.0, -0.01, 1.66))
ITEMS = {"Battery": ["SM_PVS31_BRS", "NVG_Counterweight_OpsCore_Kit", "BNVDFBat", "@Helmet Accessories/ShawBrainPouch/MC SHAWBRAIN/shawbrainpouch.fbx"],
         "Earpro": ["SM_PeltorComtac_VII_ARC", "OpsCore_AMP", "SM_Comtac_6_ARC"],
         "Scrims": ["High_Cut_Helmet_Scrim_Oak", "High_Cut_Helmet_Scrim_SemiCircle"]}
HELMETS = {"SF": (W + "/fbx/SF_Bump.fbx", W + "/fbx/SF_Rails.fbx"), "XP3": (W + "/xp/fbx/XP3_Shell.fbx", W + "/xp/fbx/XP_Rails.fbx"),
           "XP4": (W + "/xp/fbx/XP4_Shell.fbx", W + "/xp/fbx/XP_Rails.fbx"), "XPC3": (W + "/xp/fbx/XPC3_Shell.fbx", W + "/xp/fbx/XP_Rails.fbx"),
           "XPC4": (W + "/xp/fbx/XPC4_Shell.fbx", W + "/xp/fbx/XP_Rails.fbx")}


def load_bm(path):
    b = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=path)
    new = [x for x in bpy.data.objects if x not in b]
    meshes = [x for x in new if x.type == 'MESH' and not x.name.startswith(("UTM", "UCX"))]
    bm = bmesh.new()
    for o in meshes:
        me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me)
    for x in new:
        bpy.data.objects.remove(x, do_unlink=True)
    return bm


def largest_island(bm):
    bm.faces.ensure_lookup_table()
    seen = set(); best = []
    for f in bm.faces:
        if f.index in seen:
            continue
        st = [f]; comp = []; seen.add(f.index)
        while st:
            g = st.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); st.append(h)
        if len(comp) > len(best):
            best = comp
    keep = set(f.index for f in best)
    b2 = bm.copy()
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in keep], context='FACES')
    return b2


bpy.ops.wm.read_factory_settings(use_empty=True)
helm = {}
for name, (shell_p, rails_p) in HELMETS.items():
    shell = largest_island(load_bm(shell_p)); rails = load_bm(rails_p)
    helm[name] = (BVHTree.FromBMesh(shell), BVHTree.FromBMesh(rails))
report = {}
for slot, items in ITEMS.items():
    for it in items:
        path = os.path.join(OUTLAW, it[1:]) if it.startswith("@") else W + f"/fbx/{it}.fbx"
        bm = load_bm(path)
        P = [Vector(v.co) for v in bm.verts]
        row = {}
        for hn, (sh, rl) in helm.items():
            n = 0; depth = 0.0
            for p in P:
                d = p - C
                hit = sh.ray_cast(C, d.normalized(), 1.0)
                pen = 0.0
                if hit[0] is not None:
                    pen = (hit[0] - C).length - d.length
                loc, nor, idx, dist = rl.find_nearest(p, 0.02)
                if loc is not None and nor is not None:
                    pen = max(pen, -(p - loc).dot(nor))
                if pen > 0.0015:
                    n += 1; depth = max(depth, pen)
            row[hn] = {"n": n, "max_mm": round(depth * 1000, 1)}
        report[it] = {"slot": slot, "verts": len(P), **row}
        print(slot, it, {k: (v["n"], v["max_mm"]) for k, v in row.items()})
json.dump(report, open(W + "/xp/clip_report.json", "w"), indent=1)
