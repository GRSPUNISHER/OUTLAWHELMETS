"""Tiny client for the Substance Painter MCP bridge (127.0.0.1:60043) used by the OUTLAW texturing scripts.

Painter bakes on its main thread: never run a long exec (save / smart-material insert) while a bake is pending, or the exec and
the bake wait on each other and Painter hangs. bake(ts) starts ONE texture set's bake and returns only when its maps exist.
"""
import json, socket, time


def call(op, params=None, timeout=900):
    s = socket.create_connection(("127.0.0.1", 60043), timeout=timeout)
    s.sendall((json.dumps({"id": 1, "op": op, "params": params or {}}) + "\n").encode())
    buf = b""
    while b"\n" not in buf:
        buf += s.recv(1 << 20)
    r = json.loads(buf.split(b"\n")[0])
    if not r.get("ok"):
        raise RuntimeError(r)
    return r["result"]


def py(code, timeout=900):
    return call("python.exec", {"code": code}, timeout)["result"]


def wait_ready():
    while True:
        try:
            if py("import substance_painter.project as pj\nresult = pj.is_open() and not pj.is_busy()", 30):
                return
        except Exception:
            pass
        time.sleep(3)


MAPS = "('AO', 'Curvature', 'WorldSpaceNormal', 'Position', 'Thickness')"


AO_NOW = ("import substance_painter.textureset as ts\n"
          "r = ts.TextureSet.from_name('{t}').get_mesh_map_resource(ts.MeshMapUsage.AO)\nresult = str(r.url()) if r else ''")


def bake(tsname):
    """AO Self Occlusion = "Only same mesh name" (FilterMethodSecondary 1; user 2026-09-30: "thats how you get rid of the
    shadows") - separate objects such as the removable rails no longer shadow the shell. Returns once the AO map is new.
    Normal is NOT baked: like the user's MCB HELMET.spp, the Normal mesh map is the vendor _nohq (set_vendor_normals.py);
    a low-as-high normal bake is flat and made the XP rails look flat/matte."""
    before = py(AO_NOW.format(t=tsname), 30)
    py("import substance_painter.baking as bk, substance_painter.textureset as ts\n"
       f"bp = bk.BakingParameters.from_texture_set_name('{tsname}'); c = bp.common(); a = bp.baker(bk.MeshMapUsage.AO)\n"
       "bk.BakingParameters.set({c['LowAsHigh']: True, c['OutputSize']: (12, 12), a['IgnoreBackfaceSecondary']: 2, a['FilterMethodSecondary']: 1})\n"
       "bp.set_enabled_bakers([bk.MeshMapUsage.WorldSpaceNormal, bk.MeshMapUsage.AO, bk.MeshMapUsage.Curvature, bk.MeshMapUsage.Position, bk.MeshMapUsage.Thickness])\n"
       f"bk.bake_async(ts.TextureSet.from_name('{tsname}'))\nresult = 'started'")
    t0 = time.time()
    while True:
        time.sleep(5)
        try:
            done = py("import substance_painter.textureset as ts\n"
                      f"t = ts.TextureSet.from_name('{tsname}')\n"
                      f"result = all(t.get_mesh_map_resource(getattr(ts.MeshMapUsage, k)) is not None for k in {MAPS})", 30)
            done = done and py(AO_NOW.format(t=tsname), 30) != before
        except Exception:
            done = False
        if done:
            time.sleep(5)
            return time.time() - t0
