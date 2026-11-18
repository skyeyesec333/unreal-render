"""What did Unreal really store for a mesh's texture coordinates? Run it inside Unreal (headless is fine) after any
change to how meshes are imported: a log line saying a precision setting was set proves nothing.

  UnrealEditor-Cmd <project> -run=pythonscript -script=probe_uv.py -unattended -nosplash -nullrhi
  with  PROBE_FOLDER=/Game/MyCity/Landmarks  and optionally  PROBE_OUT=<file>  in the environment

For every static mesh under the folder, section by section: how many vertices, the range of u, how many distinct
values, and the smallest steps between them. With coordinates in metres, steps of whole metres (or 32 m at large
offsets) mean half-precision storage: import with an Interchange pipeline that sets use_full_precision_u_vs."""
import os
import unreal

folder = os.environ.get("PROBE_FOLDER", "/Game")
out_path = os.environ.get("PROBE_OUT", unreal.Paths.project_saved_dir() + "probe_uv.txt")
out = open(out_path, "w")
def say(s):
    out.write(str(s) + "\n"); out.flush(); unreal.log(str(s))

lib = unreal.EditorAssetLibrary
for path in lib.list_assets(folder, recursive=True):
    obj = lib.load_asset(path)
    if not isinstance(obj, unreal.StaticMesh): continue
    try:
        nanite = obj.get_editor_property("nanite_settings").get_editor_property("enabled")
        say("%s: %d triangles, %d sections, nanite %s" % (path, obj.get_num_triangles(0), obj.get_num_sections(0), nanite))
        for sec in range(obj.get_num_sections(0)):
            try:
                _, _, _, uv, _ = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(obj, 0, sec)
                us = sorted(set(round(p.x, 3) for p in uv))
                steps = sorted(set(round(b - a, 3) for a, b in zip(us, us[1:])))[:6]
                say("  section %d: %d verts, u %.3f..%.3f, %d distinct, smallest steps %s" % (sec, len(uv), us[0], us[-1], len(us), steps))
            except Exception as e:
                say("  section %d: %s" % (sec, e))
    except Exception as e:
        say("%s: %s" % (path, e))
say("written to " + out_path)
out.close()
