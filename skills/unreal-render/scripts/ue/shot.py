"""A camera, a level sequence and a Movie Render Queue config, all new for this run, in the current level.

    cam = shot.camera(at=(x, y, z), aim=(x, y, z), focal_mm=24)        # Unreal cm
    seq, cfg, out = shot.sequence_and_config(cam, "Vista", frames=24, fps=24, res=(1920, 1080))
    ur.save_level()
    shot.render_line(map_path, seq, cfg, out)    # the report line ue-remote.sh turns into a render command

The config is set for clean stills: anti-aliasing by temporal samples (8) with the engine's own AA off, long warm-up
(engine 300 frames, render 64) so streaming, Lumen and exposure have settled before frame 0, PNG output, game
overrides on. Raise the samples for motion blur; lower the warm-up only once a scene is known to settle sooner.
"""
import unreal
import ur

tools = unreal.AssetToolsHelpers.get_asset_tools()
FILMBACK = (36.0, 20.25)    # a 16:9 film back: the export below assumes the same


def camera(at, aim, focal_mm=24.0, label="Camera"):
    at_v = unreal.Vector(*at)
    rot = unreal.MathLibrary.find_look_at_rotation(at_v, unreal.Vector(*aim))
    cam = ur.spawn(unreal.CineCameraActor, at, (0, rot.pitch, rot.yaw), label="%s_%s" % (label, ur.RUN), path="MyRenders/Cameras")
    cc = cam.get_cine_camera_component()
    fb = cc.get_editor_property("filmback")
    fb.set_editor_property("sensor_width", FILMBACK[0]); fb.set_editor_property("sensor_height", FILMBACK[1])
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", float(focal_mm))
    fs = cc.get_editor_property("focus_settings")
    fs.set_editor_property("focus_method", unreal.CameraFocusMethod.DISABLE)   # everything sharp; add DOF in the config if wanted
    cc.set_editor_property("focus_settings", fs)
    return cam


def sequence_and_config(cam, prefix="Shot", frames=24, fps=24, res=(1920, 1080), warmup=(300, 64), samples=8):
    base = ur.folder("Seq")
    seq = tools.create_asset(ur.name(prefix), base, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(int(fps), 1)); seq.set_playback_start(0); seq.set_playback_end(int(frames))
    b = seq.add_possessable(cam)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack).add_section(); cut.set_range(0, int(frames))
    try:
        bid = unreal.MovieSceneSequenceExtensions.get_portable_binding_id(seq, seq, b)
    except Exception:
        bid = seq.get_binding_id(b)
    cut.set_camera_binding_id(bid)
    unreal.EditorAssetLibrary.save_loaded_asset(seq)

    out = ur.renders_dir(prefix)
    cfg = tools.create_asset(ur.name(prefix + "Cfg"), base, unreal.MoviePipelinePrimaryConfig, None)
    o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    o.set_editor_property("output_directory", unreal.DirectoryPath(out))
    o.set_editor_property("output_resolution", unreal.IntPoint(int(res[0]), int(res[1])))
    o.set_editor_property("file_name_format", "frame.{frame_number}")
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("engine_warm_up_count", int(warmup[0])); aa.set_editor_property("render_warm_up_count", int(warmup[1]))
    aa.set_editor_property("temporal_sample_count", int(samples)); aa.set_editor_property("override_anti_aliasing", True)
    aa.set_editor_property("anti_aliasing_method", unreal.AntiAliasingMethod.AAM_NONE)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    unreal.EditorAssetLibrary.save_loaded_asset(cfg)
    return seq, cfg, out


def render_line(map_path, seq, cfg, out):
    """RENDER <map> <sequence> <config> and RENDERS-TO <folder>: ue-remote.sh reads these from the report"""
    ur.say("RENDER", map_path, seq.get_path_name().split(".")[0], cfg.get_path_name().split(".")[0])
    ur.say("RENDERS-TO", out)
