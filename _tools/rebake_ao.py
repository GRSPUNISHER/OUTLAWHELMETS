"""Rebake the helmet texture sets with AO Self Occlusion = "Only same mesh name" (python _tools/rebake_ao.py [maritime xp xp4 ballistic];
Painter up; no argument = maritime xp xp4).

User 2026-09-30: "get rid of the fucking shadows from the rails on the maritime helmets" / "when you bake you go to ambient
occlusion and change the self occlusion from always to only same mesh name". The rails are their own object in every Painter
mesh, so with this setting they stop shadowing the shell (the loop panels are part of the shell object and keep their contact
shadow, which they cover). Opens each SAVED project, bakes (painter_bridge.bake sets the option), saves. Then re-export:
export_helmet_colours.py maritime / xp / xp4.
"""
import sys
import painter_bridge as pb

ROOT = "C:/Users/lebea/Documents/Github/OUTLAWHELMETS/_tools/work/"
JOBS = {"maritime": (ROOT + "maritime/painter/MT_texturing.spp", ("MT", "KitA")),
        "xp": (ROOT + "xp/painter/XP_texturing.spp", ("XP1", "Carbon1", "XP4M")),
        "xp4": (ROOT + "xp/painter/XP4_texturing.spp", ("XP1",)),
        "ballistic": (ROOT + "painter/SF_Ballistic_texturing.spp", ("SF",))}   # user: "do the same rail shadow fix on the sf ballistic"

for spp, sets in [JOBS[k] for k in (sys.argv[1:] or ("maritime", "xp", "xp4"))]:
    pb.py("import substance_painter.project as pj\nif pj.is_open(): pj.close()\n"
          f"pj.open(r'{spp}')\nresult = 'ok'")
    pb.wait_ready()
    for t in sets:
        print(spp.split("/")[-1], t, "baked in %.0fs" % pb.bake(t))
        pb.wait_ready()
    print(pb.py("import substance_painter.baking as bk\n"
                f"result = {{t: bk.BakingParameters.from_texture_set_name(t).baker(bk.MeshMapUsage.AO)['FilterMethodSecondary'].value() for t in {sets!r}}}"))
    print(pb.py("import substance_painter.project as pj\npj.save(pj.ProjectSaveMode.Full)\nresult = 'saved'"))
