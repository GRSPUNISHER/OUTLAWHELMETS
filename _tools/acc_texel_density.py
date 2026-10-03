"""Texel density (UV units per metre) of the SF Ballistic shell and the Ops-Core counterweight's fabric pouch
(Blender 4.5 headless:  blender -b --python _tools/acc_texel_density.py). The helmet MC camo is tiled CAMO_UV 1.876 across
the SF atlas (painter_ballistic.py), so repeats on another model = 1.876 * d_shell / d_model keeps the same real-world
MultiCam size. The pouch = counterweight faces whose UV centre lands on coyote fabric in the vendor texture.
Writes _tools/work/acc_variants/density.json.
"""
import bpy, bmesh, os, json
import numpy as np
from PIL import Image

T = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(T, "..", "SFHELMETS", "ASSETS", "Helmet Accessories") + "/"
OUT = os.path.join(T, "work", "acc_variants"); os.makedirs(OUT, exist_ok=True)


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    o = next(x for x in bpy.data.objects if x.type == "MESH" and not x.name.startswith(("UTM", "UCX")))
    me = o.data.copy(); me.transform(o.matrix_world)
    return me


def density(me, keep=None):
    uv = me.uv_layers[0].data
    a3 = auv = 0.0
    for p in me.polygons:
        if keep and not keep(p, uv):
            continue
        a3 += p.area
        pts = [uv[li].uv for li in p.loop_indices]
        auv += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
    return (auv / a3) ** 0.5 if a3 else 0.0, a3


shell = load(os.path.join(T, "work", "fbx", "SF_Ballistic.fbx"))
bm = bmesh.new(); bm.from_mesh(shell)
bm.faces.ensure_lookup_table()
isl, seen = [], set()
for f in bm.faces:
    if f.index in seen:
        continue
    st, g = [f], []
    seen.add(f.index)
    while st:
        x = st.pop(); g.append(x.index)
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
    isl.append(g)
big = set(max(isl, key=lambda g: sum(bm.faces[i].calc_area() for i in g)))
bm.free()
d_shell, _ = density(shell, lambda p, uv: p.index in big)

tex = np.asarray(Image.open(A + "COUNTERWEIGHT/Data/OpsCoreCounterweight_Coyote_BCR.png").convert("RGB").resize((1024, 1024)), dtype=float) / 255
mx, mn = tex.max(2), tex.min(2)
fabric = (mx > 0.18) & ((mx - mn) / np.maximum(mx, 1e-6) > 0.18)
cw = load(A + "COUNTERWEIGHT/counterweight.fbx")


def on_fabric(p, uv):
    c = sum((uv[li].uv for li in p.loop_indices), start=uv[p.loop_indices[0]].uv * 0) / len(p.loop_indices)
    x, y = min(1023, max(0, int(c.x % 1 * 1024))), min(1023, max(0, int((1 - c.y % 1) * 1024)))
    return fabric[y, x]


d_cw, a_cw = density(cw, on_fabric)
res = {"d_shell": d_shell, "d_counterweight_pouch": d_cw, "pouch_area_m2": a_cw, "camo_uv_shell": 1.876,
       "counterweight_camo_repeats": 1.876 * d_shell / d_cw}
json.dump(res, open(os.path.join(OUT, "density.json"), "w"), indent=1)
print("DENSITY", res)
