"""Export a level sequence's camera, frame by frame, for compositing on the web (three.js).

Run through ue.ps1 with an arguments file:
    {"sequence": "/Game/MyRenders/Seq/Vista_1118_093000", "focal_mm": 24}
Writes <report folder>/<sequence name>.camera.json:
    {fps, frames: [{p: [x, y, z], f: [x, y, z], u: [x, y, z], vfov}]}
position in metres, forward and up vectors, vertical field of view in degrees, all in three.js's frame.

Unreal is left-handed, centimetres, X forward, Y right, Z up; three.js is right-handed, Y up, a camera looking down -Z.
(three.x, three.y, three.z) = (ue.y, ue.z, -ue.x) / 100 swaps handedness correctly (determinant -1), and directions
map the same way, so the page builds its camera with position p, lookAt(p + f), up u, and fov = vfov.
The vertical FOV assumes the 36 x 20.25 film back shot.py sets.
"""
import json, math, os, sys
sys.path.insert(0, os.environ.get("UE_RENDER_LIB", ""))
import unreal
import ur

a = ur.args({"focal_mm": 24.0})
seq_path = ur.asset_path(a.get("sequence"))
seq = unreal.EditorAssetLibrary.load_asset(seq_path)
if seq is None:
    raise SystemExit("no sequence at " + seq_path)
fps = seq.get_display_rate(); rate = fps.numerator / fps.denominator
start, end = seq.get_playback_start(), seq.get_playback_end()
SENSOR_H = 20.25


def to_three(v):
    return [v.y / 100.0, v.z / 100.0, -v.x / 100.0]


def dir_three(v):
    return [v.y, v.z, -v.x]


binding = None
for b in seq.get_bindings():
    if any(isinstance(t, unreal.MovieScene3DTransformTrack) for t in b.get_tracks()):
        binding = b
        break

focal_chan = None
frames = []
if binding is None:
    # a camera with no animated transform: read its placement from the level (one pose for every frame)
    cams = [x for x in ur.actors() if isinstance(x, unreal.CineCameraActor)]
    bound = [x for x in cams if any(x.get_actor_label() in str(b.get_display_name()) for b in seq.get_bindings())]
    if not bound:
        raise SystemExit("no camera bound in " + seq_path)
    c = bound[0]; loc = c.get_actor_location(); rot = c.get_actor_rotation()
    focal = c.get_cine_camera_component().get_editor_property("current_focal_length")
    vfov = math.degrees(2 * math.atan(SENSOR_H / 2 / focal))
    pose = {"p": to_three(loc), "f": dir_three(rot.get_forward_vector()), "u": dir_three(rot.get_up_vector()), "vfov": round(vfov, 3)}
    frames = [pose for _ in range(start, end + 1)]
else:
    xform = [t for t in binding.get_tracks() if isinstance(t, unreal.MovieScene3DTransformTrack)][0]
    chans = xform.get_sections()[0].get_all_channels()
    names = [c.channel_name for c in chans]

    def ch(n):
        return chans[names.index(n)]

    for child in binding.get_child_possessables():
        for tr in child.get_tracks():
            if isinstance(tr, unreal.MovieSceneFloatTrack) and "Focal" in str(tr.get_property_name()):
                focal_chan = tr.get_sections()[0].get_all_channels()[0]
    for f in range(start, end + 1):
        t = unreal.FrameNumber(f)
        loc = unreal.Vector(ch("Location.X").evaluate(t), ch("Location.Y").evaluate(t), ch("Location.Z").evaluate(t))
        rot = unreal.Rotator(ch("Rotation.X").evaluate(t), ch("Rotation.Y").evaluate(t), ch("Rotation.Z").evaluate(t))
        focal = focal_chan.evaluate(t) if focal_chan else float(a["focal_mm"])
        vfov = math.degrees(2 * math.atan(SENSOR_H / 2 / focal))
        frames.append({"p": to_three(loc), "f": dir_three(rot.get_forward_vector()), "u": dir_three(rot.get_up_vector()), "vfov": round(vfov, 3)})

report = os.environ.get("UE_RENDER_REPORT") or ""
out_dir = os.path.dirname(report) or unreal.Paths.project_saved_dir()
out = os.path.join(out_dir, seq_path.split("/")[-1].split(".")[0] + ".camera.json")
with open(out, "w") as f:
    json.dump({"fps": rate, "frames": frames}, f)
ur.say("camera: %d frames at %s fps -> %s" % (len(frames), rate, out))
