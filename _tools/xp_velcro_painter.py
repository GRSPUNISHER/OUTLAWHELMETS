"""Put the XP loop panels on the user's Bebra_Velcro layer (python _tools/xp_velcro_painter.py; Painter up).

User 2026-09-30: "the boxes and bands on the maritime helmet are velcro" - on the XP / XP Carbon the top band with the tab
and the rear band are separate sheets on the shell; xp_masks.py now writes them as <set>_velcro.png. This reopens the SAVED
XP_texturing.spp (never the in-memory colourway state), gives Bebra_Velcro in XP1 / Carbon1 a mask fill from that PNG, and
saves. Re-export afterwards with export_helmet_colours.py xp.
"""
import painter_bridge as pb

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
PD = ROOT + "_tools/work/xp/painter/"

pb.py("import substance_painter.project as pj\nif pj.is_open(): pj.close()\n"
      f"pj.open(r'{PD}XP_texturing.spp')\nresult = 'ok'")
pb.wait_ready()
print(pb.py(r'''
import substance_painter.layerstack as ls, substance_painter.textureset as ts, substance_painter.resource as rs, substance_painter.project as pj
PD = %r
def proj_res(name):
    for r in rs.search(name):
        i = r.identifier()
        if i.context.startswith("project") and i.name == name:
            return i
    return rs.import_project_resource(PD + "masks/" + name + ".png", rs.Usage.TEXTURE).identifier()
out = {}
for tset in ("XP1", "Carbon1"):
    stack = ts.Stack.from_name(tset)
    grp = [n for n in ls.get_root_layer_nodes(stack) if n.get_name() == "MCB stack"][0]
    nodes = {}
    def walk(ns):
        for n in ns:
            nodes.setdefault(n.get_name(), n)
            try: walk(n.sub_layers())
            except Exception: pass
    walk([grp])
    n = nodes["Bebra_Velcro"]
    n.remove_mask()
    n.add_mask(ls.MaskBackground.Black)
    fx = ls.insert_fill(ls.InsertPosition.inside_node(n, ls.NodeStack.Mask))
    fx.set_name("XP " + tset + "_velcro")
    fx.set_source(None, proj_res(tset + "_velcro"))
    out[tset] = [e.get_name() for e in n.mask_effects()]
pj.save(pj.ProjectSaveMode.Full)
result = out
''' % PD))
