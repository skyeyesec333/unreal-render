"""Light and exposure for a scene built by script.

    rig.exposure_manual(bias=-2.0)            # a fixed exposure: auto exposure undoes night and blue hour
    rig.exposure_ev(9.0)                      # or a fixed EV100 (needs ExtendDefaultLuminanceRange, see setup.md)
    rig.night(moon_lux=1.5, fog=True)          # sky atmosphere, sky light, a moon, height fog
    rig.hide_labels(("SM_dome", "SM_sun"))    # a sample's painted sky dome ignores night settings: hide it

Notes:
  * pick ONE exposure: manual (bias) or a fixed EV range. An auto range brightens a dusk scene back into a grey day
    and the lit windows vanish.
  * EV numbers only mean EV when the project's DefaultEngine.ini has
    r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True; without it the same numbers are luminance and a
    sunlit scene comes out white.
  * emissives must be calibrated against this exposure (see materials.py).
"""
import unreal
import ur


def _pp(settings_items):
    ppv = ur.spawn(unreal.PostProcessVolume, label="Grade_" + ur.RUN, path="MyRenders/Light")
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    for k, v in settings_items:
        try:
            s.set_editor_property("override_" + k, True); s.set_editor_property(k, v)
        except Exception as e:
            ur.say("grade %s not set: %s" % (k, e))
    ppv.set_editor_property("settings", s)
    return ppv


def exposure_manual(bias=-2.0, bloom=1.0, extra=None):
    items = [("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL), ("auto_exposure_bias", float(bias)),
             ("auto_exposure_apply_physical_camera_exposure", False), ("bloom_intensity", float(bloom))]
    return _pp(items + list((extra or {}).items()))


def exposure_ev(ev, extra=None):
    items = [("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM),
             ("auto_exposure_min_brightness", float(ev)), ("auto_exposure_max_brightness", float(ev))]
    return _pp(items + list((extra or {}).items()))


def night(moon_lux=1.5, sky_light=1.0, fog=True):
    moon = ur.spawn(unreal.DirectionalLight, (0, 0, 50000), (0, -40, 40), label="Moon", path="MyRenders/Light")
    mc = moon.get_component_by_class(unreal.DirectionalLightComponent)
    mc.set_editor_property("intensity", float(moon_lux))
    mc.set_editor_property("light_color", unreal.Color(170, 190, 255, 255))
    mc.set_editor_property("atmosphere_sun_light", True)
    sky = ur.spawn(unreal.SkyLight, label="SkyLight", path="MyRenders/Light")
    sc = sky.get_component_by_class(unreal.SkyLightComponent)
    sc.set_editor_property("real_time_capture", True); sc.set_editor_property("intensity", float(sky_light))
    ur.spawn(unreal.SkyAtmosphere, label="SkyAtmosphere", path="MyRenders/Light")
    if fog:
        f = ur.spawn(unreal.ExponentialHeightFog, label="Fog", path="MyRenders/Light")
        fc = f.get_component_by_class(unreal.ExponentialHeightFogComponent)
        for k, v in dict(fog_density=0.03, fog_height_falloff=0.25, start_distance=90000.0, fog_max_opacity=0.92,
                         enable_volumetric_fog=True).items():
            try:
                fc.set_editor_property(k, v)
            except Exception as e:
                ur.say("fog %s not set: %s" % (k, e))
    return moon


def hide_labels(labels):
    """hide (never delete) actors whose label is in labels; returns how many"""
    n = 0
    for a in ur.actors():
        if a.get_actor_label() in labels:
            ur.hide(a); n += 1
    ur.say("hidden %d actor(s): %s" % (n, ", ".join(labels)))
    return n
