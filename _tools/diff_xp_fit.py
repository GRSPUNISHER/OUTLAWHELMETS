"""What the user changed in the XP attachment preview (Blender 4.5 headless:  blender -b --python _tools/diff_xp_fit.py).

Compares _tools/work/xp/XP_all_attachments_AOR1_userfix.blend with ..._orig.blend, every mesh object in world space
(open_mainfile + matrix_world, never libraries.load). Per object: best of identity / rigid / rigid+uniform scale fit, the
rigid move, and how many vertices are off that fit by more than 0.05 mm (= sculpted). Writes _tools/work/xp/fit_diff.json.
"""
import bpy, json, os
import numpy as np

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "xp")


def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, cb - R @ ca


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {}
    for o in bpy.data.objects:
        if o.type == "MESH":
            out[o.name] = (np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]),
                           [c.name for c in o.users_collection], len(o.data.polygons))
    return out


orig = snapshot(os.path.join(W, "XP_all_attachments_AOR1_orig.blend"))
user = snapshot(os.path.join(W, "XP_all_attachments_AOR1_userfix.blend"))
report = {}
for n in sorted(set(orig) | set(user)):
    if n not in orig or n not in user:
        report[n] = {"status": "added" if n in user else "removed", "collection": (user.get(n) or orig.get(n))[1]}
        continue
    V0, V = orig[n][0], user[n][0]
    if len(V0) != len(V):
        report[n] = {"status": "topology changed", "verts": [len(V0), len(V)], "collection": user[n][1]}
        continue
    fits = [(np.eye(3), 1.0, np.zeros(3))]
    R, t = kabsch(V0, V); fits.append((R, 1.0, t))
    c0, c1 = V0.mean(0), V.mean(0)
    s = float(np.sqrt(((V - c1) ** 2).sum() / ((V0 - c0) ** 2).sum()))
    R, t = kabsch(V0 * s, V); fits.append((R, s, t))
    best = None
    for R_, s_, t_ in fits:
        res = np.linalg.norm((R_ @ (V0 * s_).T).T + t_ - V, axis=1)
        if best is None or (res > 5e-5).sum() < (best[3] > 5e-5).sum():
            best = (R_, s_, t_, res)
    R, s, t, res = best
    raw = np.linalg.norm(V - V0, axis=1)
    report[n] = {"status": "unchanged" if raw.max() < 5e-5 else "changed", "collection": user[n][1], "verts": len(V),
                 "max_move_mm": round(float(raw.max()) * 1000, 2),
                 "centre_move_mm": [round(float(x) * 1000, 2) for x in V.mean(0) - V0.mean(0)],
                 "scale": round(s, 5),
                 "rot_deg": round(float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))), 3),
                 "sculpted_verts": int((res > 5e-5).sum()), "max_sculpt_mm": round(float(res.max()) * 1000, 2),
                 "faces": [orig[n][2], user[n][2]]}
json.dump(report, open(os.path.join(W, "fit_diff.json"), "w"), indent=1)
for n, r in report.items():
    print("DIFF", n, r)
