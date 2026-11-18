"""unreal-render helpers, imported by build scripts running inside UnrealEditor-Cmd (-run=pythonscript).

    import os, sys; sys.path.insert(0, os.environ["UE_RENDER_LIB"]); import ur

ue.ps1 sets these for every run:
  UE_RENDER_LIB      this folder
  UE_RENDER_ARGS     a JSON file of arguments for the script (in <work>\\args), or empty
  UE_RENDER_REPORT   where say() writes: ue.ps1 prints it when the run ends
  UE_RENDER_RENDERS  the root folder Movie Render Queue writes into

Rules these helpers keep (each one cost hours once):
  * every build makes NEW assets with a run stamp in the name: a new level, sequence, config and output folder. Nothing
    is overwritten, so any earlier render can be reproduced and compared.
  * your assets live under one /Game folder of your own (ROOT, default /Game/MyRenders): a sample project's content is
    never renamed or edited in place, so the sample can be updated from the launcher.
  * anything made by script is saved explicitly (save_new_assets): saving the level does not save new material
    instances or other assets it uses.
"""
import json, os, re, time
import unreal

ROOT = "/Game/MyRenders"
RUN = time.strftime("%m%d_%H%M%S")
_NAME = re.compile(r"^[A-Za-z0-9_]+$")
_ASSET = re.compile(r"^/Game(/[A-Za-z0-9_][A-Za-z0-9_.\-]*)+$")

_report = None


def say(*parts):
    """one line to the run's report (printed by ue.ps1) and to the Unreal log"""
    global _report
    line = " ".join(str(p) for p in parts)
    path = os.environ.get("UE_RENDER_REPORT")
    if path:
        if _report is None:
            _report = open(path, "a", encoding="utf-8")
        _report.write(line + "\n"); _report.flush()
    unreal.log("UR " + line)


def args(defaults=None):
    """the run's arguments: defaults updated by the JSON file ue.ps1 was given"""
    out = dict(defaults or {})
    path = os.environ.get("UE_RENDER_ARGS")
    if path:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise SystemExit("arguments file must hold a JSON object")
        out.update(data)
    return out


def name(prefix):
    """a fresh asset name: <prefix>_<run stamp>"""
    if not _NAME.match(prefix):
        raise SystemExit("asset name prefix: letters, digits and _ only: %r" % prefix)
    return "%s_%s" % (prefix, RUN)


def folder(sub):
    if not _NAME.match(sub):
        raise SystemExit("folder: letters, digits and _ only: %r" % sub)
    return "%s/%s" % (ROOT, sub)


def asset_path(p):
    if not isinstance(p, str) or not _ASSET.match(p):
        raise SystemExit("not an asset path under /Game: %r" % (p,))
    return p


def new_level(prefix="City"):
    """a new, empty level of its own: <ROOT>/Maps/<prefix>_<run>"""
    path = "%s/%s" % (folder("Maps"), name(prefix))
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise SystemExit("level exists already (refusing to overwrite): " + path)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.new_level(path):
        raise SystemExit("could not create level " + path)
    say("level", path)
    return path


def load_level(path):
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(asset_path(path)):
        raise SystemExit("could not load level " + path)
    return path


def save_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = les.save_current_level()
    say("saved level" if ok else "LEVEL NOT SAVED")
    if not ok:
        raise SystemExit("level save failed")


def save_new_assets(sub):
    """save every asset in <ROOT>/<sub> (material instances, data made by script): the level save does not"""
    unreal.EditorAssetLibrary.save_directory(folder(sub), only_if_is_dirty=False, recursive=True)


def renders_dir(prefix):
    """a new output folder for Movie Render Queue under UE_RENDER_RENDERS; refuses one that exists"""
    root = os.environ.get("UE_RENDER_RENDERS")
    if not root:
        raise SystemExit("UE_RENDER_RENDERS is not set (run through ue.ps1)")
    path = os.path.join(root, name(prefix)).replace("\\", "/")
    if os.path.exists(path):
        raise SystemExit("render folder exists already (refusing to overwrite): " + path)
    return path


def hide(actor):
    """set aside, never delete: hidden in game and in the editor"""
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)


def actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0), label=None, path="MyRenders"):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    if label:
        a.set_actor_label(label)
    a.set_folder_path(path)
    return a
