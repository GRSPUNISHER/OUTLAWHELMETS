"""4-hole XP texture project (python _tools/xp4_painter_setup.py; Painter up, after xp4_painter_mesh.py and xp_velcro_painter.py).

XP4_texturing.spp = a copy of XP_texturing.spp (the user's MCB stack, XP masks incl. velcro) with the mesh reloaded from
xp4_painter.fbx (4-hole shells, stroke-preserving), then XP1 rebaked, so the shell no longer carries the 3-hole shroud frame's
AO. Only XP1 is exported from it (export_helmet_colours.py xp4 -> XP1H4_<TAG>); Carbon1 / XP4M stay from XP_texturing.spp.
"""
import shutil
import painter_bridge as pb

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/"
PD = ROOT + "_tools/work/xp/painter/"

pb.py("import substance_painter.project as pj\nif pj.is_open(): pj.close()\nresult = 'ok'")
shutil.copyfile(PD + "XP_texturing.spp", PD + "XP4_texturing.spp")
pb.py(f"import substance_painter.project as pj\npj.open(r'{PD}XP4_texturing.spp')\nresult = 'ok'")
pb.wait_ready()
print(pb.py("import substance_painter.project as pj, builtins\n"
            "builtins._reload_status = []\n"
            "def _cb(s): builtins._reload_status.append(str(s))\n"
            f"pj.reload_mesh(r'{PD}xp4_painter.fbx', pj.MeshReloadingSettings(import_cameras=False, preserve_strokes=True), _cb)\n"
            "result = 'reloading'"))
pb.wait_ready()
print("reload", pb.py("import builtins, substance_painter.textureset as ts, substance_painter.project as pj\n"
                      "result = [builtins._reload_status, pj.last_imported_mesh_path(), [t.name() for t in ts.all_texture_sets()]]"))
print("XP1 baked in %.0fs" % pb.bake("XP1"))
print(pb.py("import substance_painter.project as pj\npj.save(pj.ProjectSaveMode.Full)\nresult = 'saved'"))
