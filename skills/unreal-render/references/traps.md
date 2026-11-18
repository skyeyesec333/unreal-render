# Traps (each cost hours once)

## Assets made by script

- **Materials on instanced or Nanite meshes need usage flags** (`used_with_instanced_static_meshes`, `used_with_nanite`). Without them the game renderer, which is what MRQ uses, silently swaps in the default material; the only sign is a "missing usage flag" line in the log. `materials.fresh()` sets both.
- **New assets are not saved by saving the level.** Material instances, sequences and configs made by script must be saved themselves (`unreal.EditorAssetLibrary.save_loaded_asset`, or `ur.save_new_assets(<folder>)`). Otherwise the render loads defaults.
- **Make new assets each build** (the helpers stamp names with the run time; materials go in a `Run_<stamp>` folder per build) and never overwrite; deleting old ones is the user's call. Hide old actors (`ur.hide`) instead of deleting them.

## Instances

- **Instanced components on a Blueprint holder lose their materials, then their instances, on save** (the construction script runs again). Use a plain `unreal.Actor` and add the component to the actor itself through `SubobjectDataSubsystem` (`k2_gather_subobject_data_for_instance`, `add_new_subobject`): `instances.holder()`.
- **Per-instance custom data:** add the instances first, then `set_num_custom_data_floats(n)` and `set_custom_data_value(...)`. Setting `num_custom_data_floats` as a property empties the component.
- **Speed:** each per-instance write from Python is a call into the engine. About a million custom-data values took ~30 minutes. Write only what the material reads; group by mesh and material so each holder gets one `add_instances` call.
- **Decorations follow the building as built, not its footprint.** When a kit building is scaled to fit a footprint, read its actual bounds before placing neon, signs or lights on it, or they end up inside walls.

## Light and exposure

- **EV exposure needs** `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True` in `DefaultEngine.ini`; otherwise the same numbers are luminance and a sunlit scene is white.
- **Fix the exposure** (manual with a bias, or a min = max EV range). An auto range brightens dusk back into grey day and lit windows disappear.
- **Emissives are in real-world units.** At a night exposure, lit windows in a sample city sat at tens; your own neon wants roughly 100-200 times the base colour, and at physical (EV) exposure, thousands. Calibrate with a one-frame test, then keep the numbers as parameters.
- **A sample's painted sky dome ignores night settings**: hide it and use Sky Atmosphere plus a dim moon light and a sky light.
- **Long warm-ups** (engine 300 frames, render 64) let streaming, Lumen and exposure settle before frame 0. Short warm-ups give a first frame that differs from the rest.

## Cesium and real places

- **Set the georeference's stored properties** (`origin_placement`, `origin_latitude/longitude/height`) as well as calling the setter, or the saved level keeps Cesium's default origin.
- **Move CesiumSunSky's globe anchor to the site.** It starts at latitude 0, longitude 0, so the sun is computed for the wrong place (a black sky at your afternoon).
- **Aim with Cesium's own conversion** (`transform_longitude_latitude_height_position_to_unreal`) for the camera and its target: the local frame is East +X, South +Y, Up +Z, and guessed axes point the camera away.
- **Google's 3D tiles have daylight baked in**: black at night, flat in low sun, and height-limited districts read as a carpet. Use them for a daytime far horizon; build the lit near city yourself.
- **Licences**: see references/setup.md, section 5: Cesium ion's Community plan is personal and non-commercial; Google's Photorealistic 3D Tiles need on-screen attribution and restrict content and video made from them, so offline frames for a website may not be allowed at all.

## Running headless

- `-run=pythonscript` can exit 0 after a Python traceback: `ue.ps1` also fails the run when the log shows a Python error.
- `-nullrhi` is right for builds (no GPU needed, faster) but not for anything that renders or reads GPU state; MRQ runs with `-game -RenderOffscreen`.
- One Unreal process at a time per PC: two fight over the project's files and the GPU.
- First runs compile shaders for a long time (an hour or more on a big sample); later runs reuse the cache. Give the first render a generous `--timeout`.
- A build over a large district is slow (tens of minutes); a 1080p frame of a dense city about a minute on an 8 GB card.
- **An SSH session's processes die when it closes on Windows.** `--detach` therefore hands the run to a one-off scheduled task that runs as the signed-in user (Interactive logon, no stored password), writes its output to `logs/ue-render-<stamp>.txt`, and is removed by the next call once finished (a task cannot delete itself while running). The user must be signed in at the PC; if not, `--detach` says so and removes the task. Poll with `status`.
