"""Runs INSIDE Substance Painter (exec'd over the bridge) on _tools/work/painter/SF_Ballistic_texturing.spp.

That project = the user's MCB HELMET.spp stack with the Ballistic mesh added (stroke-preserving reload) and the Ballistic's
own shell / velcro islands added to the Plastic Grainy Soft / Bebra_Velcro masks. This module only swaps colour inputs
per colourway; the stack itself is the user's.

The project is legacy colour-managed, so the API rejects uniform colours: every colour is a 32 px swatch PNG resource.
"""
import os
import substance_painter.layerstack as ls
import substance_painter.textureset as ts
import substance_painter.resource as rs
import substance_painter.export as ex

WORK = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/_tools/work/painter/"
BC = ts.ChannelType.BaseColor
UID = {"base": 839, "shell_base": 1393, "shell_fill": 1569, "velcro": 890, "nylon_fill": 2195,
       "composite_fill": 4265, "rubber": 4562, "grain": 2309}
_fx = {}
_res = {}
TSET = "SF"


def configure(uid_map, texture_set):
    """Point the helper at another project's copy of the stack (layer uids differ per project)."""
    global TSET
    UID.update(uid_map)
    TSET = texture_set
    _fx.clear()
    _res.clear()


def res(path):
    if path not in _res:
        _res[path] = rs.import_project_resource(path, rs.Usage.TEXTURE).identifier()
    return _res[path]


def colour_fx(layer_uid):
    """Colour-override Fill effect on top of a material layer's content (Rubber Raw / Plastic Base Grain have no fill)."""
    if layer_uid not in _fx:
        node = ls.get_node_by_uid(layer_uid)
        fx = ls.insert_fill(ls.InsertPosition.inside_node(node, ls.NodeStack.Content))
        fx.set_name("Colourway")
        fx.active_channels = {BC}
        _fx[layer_uid] = fx.uid()
    return ls.get_node_by_uid(_fx[layer_uid])


def set_bitmap(uid, path):
    ls.get_node_by_uid(uid).set_source(BC, res(path))


CAMO_UV = ([1.876047134399414, 2.012033462524414], 180.20008850097656, [-0.22830167412757874, -0.2566382586956024])
IDENTITY_UV = ([1.0, 1.0], 0.0, [0.0, 0.0])


def uv_set(uid, tr):
    n = ls.get_node_by_uid(uid)
    p = n.get_projection_parameters()
    t = p.uv_transformation
    t.scale, t.rotation, t.offset = tr[0], tr[1], tr[2]
    p.uv_transformation = t
    n.set_projection_parameters(p)


def apply(cfg):
    """cfg: base (vendor atlas png), shell ('bitmap', path, identity_uv) | ('swatch', path),
    swatches {velcro, nylon, composite, rubber, grain: png}"""
    set_bitmap(UID["base"], cfg["base"])
    kind, path = cfg["shell"][0], cfg["shell"][1]
    set_bitmap(UID["shell_fill"], path)
    uv_set(UID["shell_fill"], IDENTITY_UV if (kind == "bitmap" and cfg["shell"][2]) else CAMO_UV)
    sw = cfg["swatches"]
    set_bitmap(UID["velcro"], sw["velcro"])
    set_bitmap(UID["nylon_fill"], sw["nylon"])
    set_bitmap(UID["composite_fill"], sw["composite"])
    colour_fx(UID["rubber"]).set_source(BC, res(sw["rubber"]))
    colour_fx(UID["grain"]).set_source(BC, res(sw["grain"]))


def export(tag, size_log2=12, nmo=True):
    maps = [{"fileName": tag + "_BCR", "channels": [{"destChannel": c, "srcChannel": c, "srcMapType": "documentMap", "srcMapName": "basecolor"} for c in "RGB"]}]
    if nmo:
        maps.append({"fileName": tag + "_NMO", "channels": [
            {"destChannel": "R", "srcChannel": "R", "srcMapType": "virtualMap", "srcMapName": "Normal_DirectX"},
            {"destChannel": "G", "srcChannel": "G", "srcMapType": "virtualMap", "srcMapName": "Normal_DirectX"},
            {"destChannel": "B", "srcChannel": "L", "srcMapType": "documentMap", "srcMapName": "metallic"}]})
    cfg = {"exportShaderParams": False, "exportPath": WORK + "export", "defaultExportPreset": "p",
           "exportPresets": [{"name": "p", "maps": maps}], "exportList": [{"rootPath": TSET}],
           "exportParameters": [{"parameters": {"fileFormat": "png", "bitDepth": "8", "dithering": False,
                                                "sizeLog2": size_log2, "paddingAlgorithm": "infinite"}}]}
    return str(ex.export_project_textures(cfg).status)
