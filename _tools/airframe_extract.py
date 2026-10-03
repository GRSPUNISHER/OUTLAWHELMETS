"""Extract the CRYE Airframe parts from the vendor .blend (Blender 5.1: the file is a 5.0 save with geometry-nodes modifiers).

  "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b <Helmet_CRYE_Airframe.blend> --python _tools/airframe_extract.py

Writes one static FBX per part (evaluated meshes, world space, vendor frame, sub-objects joined) to _tools/work/airframe/raw/.
No transform is applied here: every part keeps the placement the .blend has (the user placed them).
"""
import bpy, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "airframe", "raw")
PARTS = {
    "AF_Shell": ["Helmet_CRYE_Airframe"],
    "AF_Cover": ["Helmet_CRYE_Airframe_Cover"],
    "AF_ComtacVII": ["EarPro_Peltor_ComTac_VII_WM"],
    "AF_Helstar": ["Helmet_Strobe_CS_HELSTAR_6_G3"],
    "AF_TNVCLight": ["Light_TNVC_Mount", "Light_TNVC_Adapter", "Light_TNVC_Right_Head", "Light_TNVC_Right_Tail"],
    "AF_OpsCoreCounterweight": ["NVG_Counterweight_OpsCore_Kit"],
    "AF_Mohawk": ["NVG_Counterweight_TNVC_Mohawk_MK3_G2", "NVG_L3Harris_BatteryPack_WM"],
    "AF_G24": ["NVG_Mount_Wilcox_G24_Body", "NVG_Mount_Wilcox_G24_Body2", "NVG_Mount_Wilcox_G24_Rack_L", "NVG_Mount_Wilcox_G24_Rack_S",
               "NVG_Mount_Wilcox_G24_Slider_L", "NVG_Mount_Wilcox_G24_Slider_S"],
}
os.makedirs(OUT, exist_ok=True)
dg = bpy.context.evaluated_depsgraph_get()
made = []
for part, names in PARTS.items():
    copies = []
    for n in names:
        o = bpy.data.objects[n]
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        c = bpy.data.objects.new(part + "_" + n, me)
        bpy.context.scene.collection.objects.link(c)
        copies.append(c)
    bpy.ops.object.select_all(action='DESELECT')
    for c in copies:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    if len(copies) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = part; j.data.name = part
    bpy.ops.object.select_all(action='DESELECT'); j.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, part + ".fbx"), use_selection=True, object_types={'MESH'},
                             mesh_smooth_type='FACE', apply_unit_scale=True, use_space_transform=True, add_leaf_bones=False, bake_anim=False)
    made.append((part, len(j.data.vertices), [m.name for m in j.data.materials], [u.name for u in j.data.uv_layers]))
for m in made:
    print("PART", m)
